from celery import shared_task


@shared_task
def expire_old_carts():
    """Soft-clear carts that have been expired for more than 7 days."""
    from django.utils import timezone
    from datetime import timedelta
    from .models import Cart
    cutoff = timezone.now() - timedelta(days=7)
    expired = Cart.objects.filter(updated_at__lt=cutoff)
    count = 0
    for cart in expired:
        if cart.is_expired:
            cart.items.all().delete()
            cart.coupon = None
            cart.save()
            count += 1
    return f'Cleared {count} expired carts.'
