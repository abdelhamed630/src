import hashlib
import secrets
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        BUYER  = 'buyer',  'Buyer'
        SELLER = 'seller', 'Seller'

    email        = models.EmailField(unique=True)
    full_name    = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role         = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)

    is_active    = models.BooleanField(default=False)
    is_verified  = models.BooleanField(default=False)
    is_staff     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    google_id     = models.CharField(max_length=255, blank=True, null=True, unique=True)
    auth_provider = models.CharField(max_length=50, default='email')

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_seller(self):
        return self.role == self.Role.SELLER

    @property
    def is_buyer(self):
        return self.role == self.Role.BUYER


class SellerProfile(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending Review'
        APPROVED  = 'approved',  'Approved'
        REJECTED  = 'rejected',  'Rejected'
        SUSPENDED = 'suspended', 'Suspended'

    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    store_name    = models.CharField(max_length=255)
    store_slug    = models.SlugField(max_length=255, unique=True, blank=True)
    store_logo    = models.ImageField(upload_to='sellers/logos/', blank=True, null=True)
    store_banner  = models.ImageField(upload_to='sellers/banners/', blank=True, null=True)
    description   = models.TextField(blank=True)
    national_id   = models.CharField(max_length=50)
    status        = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_notes   = models.TextField(blank=True)
    bank_account  = models.CharField(max_length=100, blank=True)
    bank_name     = models.CharField(max_length=100, blank=True)
    total_sales   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders  = models.PositiveIntegerField(default=0)
    rating        = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.store_name} ({self.user.email})'

    def save(self, *args, **kwargs):
        if not self.store_slug:
            from django.utils.text import slugify
            self.store_slug = slugify(self.store_name)
        super().save(*args, **kwargs)

    @property
    def is_active_store(self):
        return self.status == self.Status.APPROVED


class SellerRequest(models.Model):
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_request')
    store_name   = models.CharField(max_length=255)
    description  = models.TextField()
    national_id  = models.CharField(max_length=50)
    phone        = models.CharField(max_length=20)
    bank_account = models.CharField(max_length=100, blank=True)
    bank_name    = models.CharField(max_length=100, blank=True)
    status       = models.CharField(
        max_length=20,
        choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')],
        default='pending'
    )
    admin_notes  = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    reviewed_at  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'SellerRequest: {self.user.email} [{self.status}]'


class Address(models.Model):
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label         = models.CharField(max_length=50, default='Home')
    full_name     = models.CharField(max_length=255)
    phone         = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100, blank=True)
    postal_code   = models.CharField(max_length=20, blank=True)
    country       = models.CharField(max_length=100, default='Egypt')
    is_default    = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.label} - {self.city}, {self.country}'


class OTPCode(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code_hash  = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts   = models.PositiveSmallIntegerField(default=0)
    is_used    = models.BooleanField(default=False)

    MAX_ATTEMPTS = 5
    OTP_LIFETIME = timedelta(minutes=5)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expires_at = timezone.now() + self.OTP_LIFETIME
        super().save(*args, **kwargs)

    @staticmethod
    def hash_otp(raw_otp: str) -> str:
        return hashlib.sha256(raw_otp.encode()).hexdigest()

    @staticmethod
    def generate_otp() -> str:
        return str(secrets.randbelow(900000) + 100000)

    def is_valid(self) -> bool:
        return (
            not self.is_used
            and self.attempts < self.MAX_ATTEMPTS
            and timezone.now() < self.expires_at
        )

    def verify(self, raw_otp: str) -> bool:
        self.attempts += 1
        if self.code_hash == self.hash_otp(raw_otp) and self.is_valid():
            self.is_used = True
            self.save()
            return True
        self.save()
        return False
