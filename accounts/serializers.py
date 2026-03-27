from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Address, SellerRequest, SellerProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password     = serializers.CharField(write_only=True, validators=[validate_password])
    password2    = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model  = User
        fields = ['full_name', 'phone_number', 'email', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(
            email        = validated_data['email'],
            password     = validated_data['password'],
            full_name    = validated_data['full_name'],
            phone_number = validated_data.get('phone_number'),
            is_active    = False,
        )


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp   = serializers.CharField(min_length=6, max_length=6)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'role', 'is_verified', 'auth_provider', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'auth_provider', 'created_at']


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password  = serializers.CharField(write_only=True)
    new_password  = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email         = serializers.EmailField()
    otp           = serializers.CharField(min_length=6, max_length=6)
    new_password  = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class SellerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SellerRequest
        fields = ['store_name', 'description', 'national_id', 'phone', 'bank_account', 'bank_name']


class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SellerProfile
        fields = ['store_name', 'store_slug', 'store_logo', 'store_banner',
                  'description', 'total_sales', 'total_orders', 'rating',
                  'reviews_count', 'status']
        read_only_fields = ['store_slug', 'total_sales', 'total_orders', 'rating', 'reviews_count', 'status']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Address
        fields = ['id', 'label', 'full_name', 'phone', 'address_line1', 'address_line2',
                  'city', 'state', 'postal_code', 'country', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']
