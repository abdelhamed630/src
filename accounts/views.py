from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings

from .models import OTPCode, SellerRequest, SellerProfile, Address
from .serializers import (
    RegisterSerializer, VerifyOTPSerializer,
    ResendOTPSerializer, LoginSerializer,
    UserSerializer, GoogleAuthSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    SellerRequestSerializer, AddressSerializer,
)
from .utils import send_otp_email

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    role = 'admin' if (user.is_staff or user.is_superuser) else user.role
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'role': role,
        'is_staff': user.is_staff,
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': role,
            'is_staff': user.is_staff,
        }
    }


# ── Register ──────────────────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        raw_otp = OTPCode.generate_otp()
        OTPCode.objects.create(user=user, code_hash=OTPCode.hash_otp(raw_otp))
        send_otp_email(user.email, raw_otp)
        return Response({'detail': 'Account created. Check your email for the OTP.'}, status=status.HTTP_201_CREATED)


# ── Verify OTP ────────────────────────────────────────────────────────
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email, raw_otp = serializer.validated_data['email'], serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        otp_obj = OTPCode.objects.filter(user=user, is_used=False).order_by('-created_at').first()
        if not otp_obj or not otp_obj.is_valid():
            return Response({'detail': 'OTP expired or invalid.'}, status=status.HTTP_400_BAD_REQUEST)
        if not otp_obj.verify(raw_otp):
            remaining = otp_obj.MAX_ATTEMPTS - otp_obj.attempts
            return Response({'detail': f'Invalid OTP. {remaining} attempts remaining.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.is_verified = True
        user.save()
        return Response({'detail': 'Email verified successfully.', **get_tokens_for_user(user)})


# ── Resend OTP ────────────────────────────────────────────────────────
class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    COOLDOWN_SECONDS = 60

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user.is_verified:
            return Response({'detail': 'Account already verified.'}, status=status.HTTP_400_BAD_REQUEST)
        last_otp = OTPCode.objects.filter(user=user).order_by('-created_at').first()
        if last_otp:
            cooldown_end = last_otp.created_at + timedelta(seconds=self.COOLDOWN_SECONDS)
            if timezone.now() < cooldown_end:
                wait = int((cooldown_end - timezone.now()).total_seconds())
                return Response({'detail': f'Please wait {wait} seconds.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        raw_otp = OTPCode.generate_otp()
        OTPCode.objects.create(user=user, code_hash=OTPCode.hash_otp(raw_otp))
        send_otp_email(user.email, raw_otp)
        return Response({'detail': 'New OTP sent.'})


# ── Login ─────────────────────────────────────────────────────────────
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email, password = serializer.validated_data['email'], serializer.validated_data['password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_verified:
            return Response({'detail': 'Account not verified.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(get_tokens_for_user(user))


# ── Google OAuth ──────────────────────────────────────────────────────
class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        try:
            id_info = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
        except ValueError:
            return Response({'detail': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)
        google_id = id_info.get('sub')
        email = id_info.get('email')
        if not email:
            return Response({'detail': 'Could not retrieve email from Google.'}, status=status.HTTP_400_BAD_REQUEST)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'google_id': google_id, 'auth_provider': 'google', 'is_active': True, 'is_verified': True}
        )
        if not created and not user.google_id:
            user.google_id = google_id
            user.auth_provider = 'google'
            user.is_verified = True
            user.is_active = True
            user.save()
        return Response({'detail': 'Google login successful.', **get_tokens_for_user(user)})


# ── Logout ────────────────────────────────────────────────────────────
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
            return Response({'detail': 'Logged out successfully.'})
        except Exception:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


# ── Profile ───────────────────────────────────────────────────────────
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── Change Password ───────────────────────────────────────────────────
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'detail': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password changed successfully.'})


# ── Forgot / Reset Password ───────────────────────────────────────────
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    COOLDOWN_SECONDS = 60

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'If this email exists, an OTP has been sent.'})
        last_otp = OTPCode.objects.filter(user=user).order_by('-created_at').first()
        if last_otp:
            cooldown_end = last_otp.created_at + timedelta(seconds=self.COOLDOWN_SECONDS)
            if timezone.now() < cooldown_end:
                wait = int((cooldown_end - timezone.now()).total_seconds())
                return Response({'detail': f'Wait {wait}s before requesting a new OTP.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        raw_otp = OTPCode.generate_otp()
        OTPCode.objects.create(user=user, code_hash=OTPCode.hash_otp(raw_otp))
        send_otp_email(user.email, raw_otp)
        return Response({'detail': 'If this email exists, an OTP has been sent.'})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email, raw_otp = serializer.validated_data['email'], serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        otp_obj = OTPCode.objects.filter(user=user, is_used=False).order_by('-created_at').first()
        if not otp_obj or not otp_obj.is_valid():
            return Response({'detail': 'OTP expired or invalid.'}, status=status.HTTP_400_BAD_REQUEST)
        if not otp_obj.verify(raw_otp):
            remaining = otp_obj.MAX_ATTEMPTS - otp_obj.attempts
            return Response({'detail': f'Invalid OTP. {remaining} attempts remaining.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password reset successfully.'})


# ── Seller Request ────────────────────────────────────────────────────
class SellerRequestView(APIView):
    """
    POST /accounts/seller-request/ — buyer submits request to become a seller.
    Only buyers can apply. Admin must approve via admin panel.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role == 'seller':
            return Response({'detail': 'You are already a seller.'}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(user, 'seller_request') and user.seller_request.status == 'pending':
            return Response({'detail': 'You already have a pending seller request.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SellerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        SellerRequest.objects.update_or_create(
            user=user,
            defaults={**serializer.validated_data, 'status': 'pending'}
        )
        return Response({'detail': 'Seller request submitted. We will review and get back to you within 3 business days.'}, status=status.HTTP_201_CREATED)

    def get(self, request):
        """Check own seller request status"""
        if not hasattr(request.user, 'seller_request'):
            return Response({'detail': 'No seller request found.'}, status=status.HTTP_404_NOT_FOUND)
        req = request.user.seller_request
        return Response({
            'status': req.status,
            'store_name': req.store_name,
            'submitted_at': req.created_at,
            'admin_notes': req.admin_notes if req.status != 'pending' else '',
        })


# ── Address CRUD ──────────────────────────────────────────────────────
class AddressListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = request.user.addresses.all()
        return Response(AddressSerializer(addresses, many=True).data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_address(self, user, pk):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Address, id=pk, user=user)

    def patch(self, request, pk):
        addr = self._get_address(request.user, pk)
        serializer = AddressSerializer(addr, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self._get_address(request.user, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Admin Views ────────────────────────────────────────────────────────
from rest_framework.permissions import IsAdminUser
from django.core.paginator import Paginator

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        search = request.query_params.get('search', '')
        users = User.objects.all().order_by('-created_at')
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(full_name__icontains=search)
            )
        data = [{
            'id': u.id,
            'email': u.email,
            'full_name': u.full_name,
            'role': 'admin' if u.is_staff else u.role,
            'is_active': u.is_active,
            'is_staff': u.is_staff,
            'created_at': u.created_at,
        } for u in users]
        return Response({'results': data, 'count': len(data)})

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
            user.save()
        return Response({'detail': 'Updated.'})


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
        if 'role' in request.data:
            user.role = request.data['role']
        user.save()
        return Response({'detail': 'Updated.'})

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response({'detail': 'Deleted.'})
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)


class AdminSellerRequestListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        requests_qs = SellerRequest.objects.select_related('user').order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            requests_qs = requests_qs.filter(status=status_filter)
        data = [{
            'id': r.id,
            'user': {'id': r.user.id, 'email': r.user.email, 'full_name': r.user.full_name},
            'store_name': r.store_name,
            'description': r.description,
            'national_id': r.national_id,
            'phone': r.phone,
            'bank_name': r.bank_name,
            'bank_account': r.bank_account,
            'status': r.status,
            'admin_notes': r.admin_notes,
            'created_at': r.created_at,
            'reviewed_at': r.reviewed_at,
        } for r in requests_qs]
        return Response({'results': data, 'count': len(data)})


class AdminSellerRequestDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        from django.utils import timezone as tz
        try:
            seller_req = SellerRequest.objects.select_related('user').get(pk=pk)
        except SellerRequest.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes', '')

        if new_status not in ['approved', 'rejected', 'pending']:
            return Response({'detail': 'Invalid status.'}, status=400)

        seller_req.status = new_status
        seller_req.admin_notes = admin_notes
        seller_req.reviewed_at = tz.now()
        seller_req.save()

        # If approved, change user role to seller
        if new_status == 'approved':
            user = seller_req.user
            user.role = 'seller'
            user.save()
            # Create SellerProfile if not exists
            SellerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'store_name': seller_req.store_name,
                    'description': seller_req.description,
                    'national_id': seller_req.national_id,
                    'bank_account': seller_req.bank_account,
                    'bank_name': seller_req.bank_name,
                    'status': 'approved',
                }
            )

        return Response({'detail': f'Request {new_status}.', 'status': new_status})
