from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.db.models import Q
from .models import Category, Product
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer
)

from rest_framework.permissions import IsAuthenticated





# ── Categories ────────────────────────────────────────────────────────
class CategoryListView(APIView):
    """
    GET /products/categories/
    بيرجع شجرة الـ categories من الـ root بس (الـ children جوا كل واحدة)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Root categories فقط (اللي ملهاش parent)
        categories = Category.objects.filter(parent=None, is_active=True)
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)


# ── Products ──────────────────────────────────────────────────────────
class ProductListView(APIView):
    """
    GET /products/
    Supports:
        ?search=      — بحث في الاسم والوصف
        ?category=    — slug الـ category
        ?tag=         — slug الـ tag
        ?featured=true
        ?best_seller=true
        ?on_sale=true
        ?type=physical|digital
        ?ordering=price|-price|newest
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'tags')

        # Search
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

        # Category (بيشمل الـ subcategories تلقائياً)
        category_slug = request.query_params.get('category')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                # نجيب كل الـ categories اللي تحتيها
                category_ids = self._get_category_tree_ids(category)
                qs = qs.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                qs = qs.none()

        # Tag
        tag_slug = request.query_params.get('tag')
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        # Flags
        if request.query_params.get('featured') == 'true':
            qs = qs.filter(is_featured=True)
        if request.query_params.get('best_seller') == 'true':
            qs = qs.filter(is_best_seller=True)
        if request.query_params.get('on_sale') == 'true':
            qs = qs.exclude(discount_price=None)

        # Product type
        product_type = request.query_params.get('type')
        if product_type in ['physical', 'digital']:
            qs = qs.filter(product_type=product_type)

        # Ordering
        ordering = request.query_params.get('ordering', 'newest')
        ordering_map = {
            'newest' : '-created_at',
            'price'  : 'base_price',
            '-price' : '-base_price',
        }
        qs = qs.order_by(ordering_map.get(ordering, '-created_at'))

        serializer = ProductListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def _get_category_tree_ids(self, category):
        """بيرجع الـ category نفسها + كل الـ children بشكل recursive"""
        ids = [category.id]
        for child in category.children.filter(is_active=True):
            ids.extend(self._get_category_tree_ids(child))
        return ids


class ProductDetailView(APIView):
    """
    GET /products/<slug>/
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            product = (
                Product.objects
                .filter(is_active=True)
                .prefetch_related('images', 'variants__attribute_values__attribute', 'tags', 'related_products__images')
                .select_related('category')
                .get(slug=slug)
            )
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response(serializer.data)


class FeaturedProductsView(APIView):
    """GET /products/featured/"""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Product.objects.filter(is_active=True, is_featured=True).prefetch_related('images').select_related('category')
        serializer = ProductListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class BestSellerProductsView(APIView):
    """GET /products/best-sellers/"""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Product.objects.filter(is_active=True, is_best_seller=True).prefetch_related('images').select_related('category')
        serializer = ProductListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class OnSaleProductsView(APIView):
    """GET /products/on-sale/"""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            Product.objects
            .filter(is_active=True)
            .exclude(discount_price=None)
            .prefetch_related('images')
            .select_related('category')
        )
        serializer = ProductListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


# ── Seller: Manage Own Products ───────────────────────────────────────
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import ProductDetailSerializer


class SellerProductListView(APIView):
    """
    GET  /products/my-products/    — seller sees their own products
    POST /products/my-products/    — seller creates a new product
    """
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def get(self, request):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)
        qs = Product.objects.filter(seller=request.user).prefetch_related('images', 'tags', 'variants').select_related('category')
        return Response(ProductListSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)
        from .serializers import ProductCreateSerializer
        serializer = ProductCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save(seller=request.user)
        return Response(ProductDetailSerializer(product, context={'request': request}).data, status=status.HTTP_201_CREATED)


class SellerProductDetailView(APIView):
    """
    PATCH  /products/my-products/<slug>/ — seller edits their product
    DELETE /products/my-products/<slug>/ — seller deletes their product
    """
    permission_classes = [IsAuthenticated]

    def _get_product(self, user, slug):
        return get_object_or_404(Product, slug=slug, seller=user)

    def patch(self, request, slug):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)
        product = self._get_product(request.user, slug)
        from .serializers import ProductCreateSerializer
        serializer = ProductCreateSerializer(product, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductDetailSerializer(product, context={'request': request}).data)

    def delete(self, request, slug):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)
        product = self._get_product(request.user, slug)
        # Soft delete
        product.is_active = False
        product.save()
        return Response({'detail': 'Product removed from store.'})


# ── Search with Suggestions ───────────────────────────────────────────
class SearchSuggestionsView(APIView):
    """
    GET /products/search/suggestions/?q=shoes
    Returns fast autocomplete suggestions (product names + categories)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'products': [], 'categories': []})

        from django.db.models import Q
        products = (
            Product.objects
            .filter(is_active=True)
            .filter(Q(name__icontains=q) | Q(tags__name__icontains=q))
            .values('name', 'slug')
            .distinct()[:8]
        )
        from .models import Category
        categories = (
            Category.objects
            .filter(is_active=True, name__icontains=q)
            .values('name', 'slug')[:4]
        )
        return Response({
            'products'  : list(products),
            'categories': list(categories),
        })
