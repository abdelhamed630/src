from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator
import uuid


# ── Category ──────────────────────────────────────────────────────────
class Category(models.Model):
    name       = models.CharField(max_length=255)
    slug       = models.SlugField(max_length=255, unique=True, blank=True)
    parent     = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='children'
    )
    image      = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if self.image and hasattr(self.image, 'file'):
            try:
                from .image_utils import process_image
                self.image = process_image(self.image, watermark=False)
            except Exception:
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f'{self.parent} > {self.name}'
        return self.name

    @property
    def level(self):
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level


# ── Tag ───────────────────────────────────────────────────────────────
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ── Product ───────────────────────────────────────────────────────────
class Product(models.Model):
    class ProductType(models.TextChoices):
        PHYSICAL = 'physical', 'Physical'
        DIGITAL  = 'digital',  'Digital'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category     = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    tags         = models.ManyToManyField('Tag', blank=True, related_name='products')

    name         = models.CharField(max_length=255)
    slug         = models.SlugField(max_length=255, unique=True, blank=True)
    description  = models.TextField(blank=True)
    product_type = models.CharField(max_length=20, choices=ProductType.choices, default=ProductType.PHYSICAL)

    base_price     = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])

    digital_file   = models.FileField(upload_to='products/digital/', blank=True, null=True)

    is_active      = models.BooleanField(default=True)
    is_featured    = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)

    # Seller who owns this product
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
        limit_choices_to={'role': 'seller'},
    )

    related_products = models.ManyToManyField('self', blank=True, symmetrical=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.base_price

    @property
    def discount_percentage(self):
        if self.discount_price and self.base_price > 0:
            return round((1 - self.discount_price / self.base_price) * 100)
        return 0

    @property
    def is_on_sale(self):
        return bool(self.discount_price and self.discount_price < self.base_price)


# ── Product Image ─────────────────────────────────────────────────────
class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image      = models.ImageField(upload_to='products/images/')
    thumbnail  = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)
    alt_text   = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        # لو primary، شيل primary من الباقيين
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)

        # معالجة الصورة لو صورة جديدة
        if self.image and hasattr(self.image, 'file'):
            try:
                from .image_utils import process_image, make_thumbnail

                # الصورة الأساسية مع watermark
                processed   = process_image(self.image, watermark=True)
                self.image  = processed

                # Thumbnail بدون watermark — بنحتاج نفتح الصورة من الأول
                from django.core.files.base import ContentFile
                from io import BytesIO
                from PIL import Image as PilImage

                processed.seek(0)
                pil_img   = PilImage.open(processed)
                thumb_buf = BytesIO()
                pil_img.thumbnail((400, 400))
                pil_img.save(thumb_buf, format='WEBP', quality=80)
                thumb_buf.seek(0)

                import os
                base_name      = os.path.splitext(processed.name)[0]
                self.thumbnail = ContentFile(thumb_buf.read(), name=f'{base_name}_thumb.webp')

            except Exception:
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.name} - Image {self.order}'


# ── Attribute ─────────────────────────────────────────────────────────
class Attribute(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value     = models.CharField(max_length=100)

    class Meta:
        unique_together = ('attribute', 'value')

    def __str__(self):
        return f'{self.attribute.name}: {self.value}'


# ── Product Variant ───────────────────────────────────────────────────
class ProductVariant(models.Model):
    product          = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku              = models.CharField(max_length=100, unique=True)
    attribute_values = models.ManyToManyField(AttributeValue, blank=True)

    price_override   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock            = models.PositiveIntegerField(default=0)
    is_active        = models.BooleanField(default=True)

    class Meta:
        ordering = ['sku']

    def __str__(self):
        attrs = ', '.join(str(av) for av in self.attribute_values.all())
        return f'{self.product.name} [{attrs}] - SKU: {self.sku}'

    @property
    def effective_price(self):
        return self.price_override if self.price_override else self.product.effective_price

    @property
    def in_stock(self):
        return self.stock > 0


# ── Seller Link (added) ───────────────────────────────────────────────
# Add seller FK to Product via migration
# This is patched here for reference — add via migration
