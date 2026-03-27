from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.html import format_html
from .models import User, OTPCode, SellerProfile, SellerRequest, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display    = ['email', 'full_name', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter     = ['role', 'is_verified', 'is_active', 'auth_provider']
    search_fields   = ['email', 'full_name']
    ordering        = ['-created_at']
    readonly_fields = ['created_at', 'last_login']

    fieldsets = (
        (None,         {'fields': ('email', 'password')}),
        ('Personal',   {'fields': ('full_name', 'phone_number', 'role')}),
        ('OAuth',      {'fields': ('google_id', 'auth_provider')}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates',      {'fields': ('created_at', 'last_login')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'full_name', 'role', 'password1', 'password2')}),
    )


@admin.register(SellerRequest)
class SellerRequestAdmin(admin.ModelAdmin):
    list_display  = ['user', 'store_name', 'status', 'created_at', 'approve_action']
    list_filter   = ['status']
    search_fields = ['user__email', 'store_name']
    readonly_fields = ['user', 'store_name', 'description', 'national_id', 'phone', 'created_at']
    actions       = ['approve_requests', 'reject_requests']

    def approve_action(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="approve/{}/" style="background:#28a745;color:white;padding:3px 8px;border-radius:4px;">✓ Approve</a>',
                obj.id
            )
        return format_html('<span style="color:grey">{}</span>', obj.status.title())
    approve_action.short_description = 'Action'

    def approve_requests(self, request, queryset):
        for req in queryset.filter(status='pending'):
            self._approve(req)
        self.message_user(request, f'{queryset.count()} seller request(s) approved.')
    approve_requests.short_description = 'Approve selected requests'

    def reject_requests(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected', reviewed_at=timezone.now())
        self.message_user(request, 'Requests rejected.')
    reject_requests.short_description = 'Reject selected requests'

    def _approve(self, req):
        req.status = 'approved'
        req.reviewed_at = timezone.now()
        req.save()
        user = req.user
        user.role = 'seller'
        user.save(update_fields=['role'])
        SellerProfile.objects.get_or_create(
            user=user,
            defaults={
                'store_name': req.store_name,
                'national_id': req.national_id,
                'bank_account': req.bank_account,
                'bank_name': req.bank_name,
                'status': 'approved',
            }
        )


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display  = ['store_name', 'user', 'status', 'total_orders', 'total_sales', 'rating']
    list_filter   = ['status']
    search_fields = ['store_name', 'user__email']
    readonly_fields = ['total_sales', 'total_orders', 'rating', 'reviews_count', 'created_at', 'updated_at']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display  = ['user', 'label', 'city', 'country', 'is_default']
    list_filter   = ['country', 'is_default']
    search_fields = ['user__email', 'city', 'full_name']


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display  = ['user', 'created_at', 'expires_at', 'attempts', 'is_used']
    list_filter   = ['is_used']
    search_fields = ['user__email']
    readonly_fields = ['user', 'code_hash', 'created_at', 'expires_at', 'attempts', 'is_used']
