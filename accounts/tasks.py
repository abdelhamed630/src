from celery import shared_task


@shared_task
def cleanup_expired_otps():
    """Delete expired OTP codes daily to keep the table clean."""
    from django.utils import timezone
    from .models import OTPCode
    deleted, _ = OTPCode.objects.filter(expires_at__lt=timezone.now()).delete()
    return f'Deleted {deleted} expired OTP codes.'
