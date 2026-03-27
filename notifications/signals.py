"""
Auto-send notifications on key events using Django signals.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='orders.Order')
def notify_order_status_change(sender, instance, created, **kwargs):
    from .models import Notification
    if created:
        Notification.send(
            user  = instance.buyer,
            type  = Notification.Type.ORDER_PLACED,
            title = f'Order #{instance.order_number} placed!',
            body  = f'Your order has been placed successfully. Total: ${instance.total}',
            link  = f'/orders/{instance.order_number}',
        )


@receiver(post_save, sender='orders.OrderItem')
def notify_item_shipped(sender, instance, created, **kwargs):
    if not created and instance.item_status == 'shipped':
        from .models import Notification
        Notification.send(
            user  = instance.order.buyer,
            type  = Notification.Type.ORDER_SHIPPED,
            title = f'"{instance.product_name}" has been shipped!',
            body  = f'Tracking number: {instance.tracking_number or "N/A"}',
            link  = f'/orders/{instance.order.order_number}',
        )
        # Also notify seller of delivered status (buyer confirmation)
    elif not created and instance.item_status == 'delivered':
        from .models import Notification
        Notification.send(
            user  = instance.order.buyer,
            type  = Notification.Type.ORDER_DELIVERED,
            title = f'"{instance.product_name}" delivered!',
            body  = 'Please leave a review if you enjoyed the product.',
            link  = f'/products/{instance.product_slug}',
        )


@receiver(post_save, sender='chat.Message')
def notify_new_message(sender, instance, created, **kwargs):
    if not created:
        return
    from .models import Notification
    convo    = instance.conversation
    receiver = convo.seller if instance.sender == convo.buyer else convo.buyer
    Notification.send(
        user  = receiver,
        type  = Notification.Type.NEW_MESSAGE,
        title = f'New message from {instance.sender.full_name}',
        body  = instance.content[:100],
        link  = f'/chat/{convo.id}',
    )


@receiver(post_save, sender='accounts.SellerRequest')
def notify_seller_decision(sender, instance, created, **kwargs):
    if created:
        return
    from .models import Notification
    if instance.status == 'approved':
        Notification.send(
            user  = instance.user,
            type  = Notification.Type.SELLER_APPROVED,
            title = '🎉 Seller request approved!',
            body  = f'Your store "{instance.store_name}" is now live. Start adding products!',
            link  = '/seller/dashboard',
        )
    elif instance.status == 'rejected':
        Notification.send(
            user  = instance.user,
            type  = Notification.Type.SELLER_REJECTED,
            title = 'Seller request rejected',
            body  = instance.admin_notes or 'Your seller request was not approved at this time.',
            link  = '/seller-request',
        )
