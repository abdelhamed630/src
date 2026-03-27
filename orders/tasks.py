"""
Celery tasks for order-related async operations.
"""
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: str):
    """Send order confirmation email to buyer."""
    try:
        from .models import Order
        order = Order.objects.prefetch_related('items').get(id=order_id)
        user  = order.buyer

        subject = f'✅ Order Confirmed — #{order.order_number}'
        body = f"""
Hi {user.full_name},

Your order #{order.order_number} has been placed successfully!

Order Total: ${order.total}
Payment Method: {order.get_payment_method_display()}
Shipping to: {order.full_shipping_address}

Items:
{chr(10).join(f"  - {i.product_name} x{i.quantity} = ${i.total_price}" for i in order.items.all())}

You can track your order in your dashboard.
Thank you for shopping with us!

— ShopZone Team
        """

        msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.send()

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_invoice_email(self, order_id: str, to_email: str):
    """Send invoice PDF to buyer or seller via email."""
    try:
        from .models import Order
        from .pdf_utils import generate_invoice_pdf

        order  = Order.objects.prefetch_related('items').get(id=order_id)
        buffer = generate_invoice_pdf(order)

        subject = f'📄 Invoice for Order #{order.order_number}'
        body    = f'Please find attached the invoice for order #{order.order_number}.'

        msg = EmailMultiAlternatives(
            subject=subject, body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach(
            f'invoice_{order.order_number}.pdf',
            buffer.read(),
            'application/pdf'
        )
        msg.send()

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def notify_seller_new_order(order_item_id: int):
    """Notify seller when a new order comes in for their product."""
    try:
        from .models import OrderItem
        from django.core.mail import send_mail

        item   = OrderItem.objects.select_related('order', 'seller').get(id=order_item_id)
        seller = item.seller
        order  = item.order

        send_mail(
            subject=f'🛒 New Order — {item.product_name}',
            message=f"""
Hi {seller.full_name},

You have a new order!

Product: {item.product_name}
Quantity: {item.quantity}
Total: ${item.total_price}
Order #: {order.order_number}
Buyer City: {order.shipping_city}

Log in to your seller dashboard to process this order.

— ShopZone Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[seller.email],
            fail_silently=True,
        )
    except Exception:
        pass
