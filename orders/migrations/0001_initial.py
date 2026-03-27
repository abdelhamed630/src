import uuid
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0003_product_seller'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order_number', models.CharField(blank=True, max_length=20, unique=True)),
                ('shipping_name', models.CharField(max_length=255)),
                ('shipping_phone', models.CharField(max_length=20)),
                ('shipping_address1', models.CharField(max_length=255)),
                ('shipping_address2', models.CharField(blank=True, max_length=255)),
                ('shipping_city', models.CharField(max_length=100)),
                ('shipping_state', models.CharField(blank=True, max_length=100)),
                ('shipping_postal', models.CharField(blank=True, max_length=20)),
                ('shipping_country', models.CharField(default='Egypt', max_length=100)),
                ('status', models.CharField(
                    choices=[('pending','Pending Payment'),('confirmed','Confirmed'),('processing','Processing'),
                             ('shipped','Shipped'),('delivered','Delivered'),('cancelled','Cancelled'),('refunded','Refunded')],
                    default='pending', max_length=20
                )),
                ('payment_method', models.CharField(
                    choices=[('cod','Cash on Delivery'),('credit_card','Credit Card'),('instapay','InstaPay'),('vodafone','Vodafone Cash')],
                    default='cod', max_length=20
                )),
                ('payment_status', models.CharField(
                    choices=[('unpaid','Unpaid'),('paid','Paid'),('refunded','Refunded')],
                    default='unpaid', max_length=20
                )),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('coupon_code', models.CharField(blank=True, max_length=50)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('shipped_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('buyer', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='orders', to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('product_name', models.CharField(max_length=255)),
                ('product_slug', models.CharField(blank=True, max_length=255)),
                ('variant_sku', models.CharField(blank=True, max_length=100)),
                ('variant_attrs', models.JSONField(default=dict)),
                ('product_image', models.URLField(blank=True)),
                ('quantity', models.PositiveSmallIntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('item_status', models.CharField(
                    choices=[('pending','Pending'),('processing','Processing'),('shipped','Shipped'),
                             ('delivered','Delivered'),('cancelled','Cancelled')],
                    default='pending', max_length=20
                )),
                ('tracking_number', models.CharField(blank=True, max_length=100)),
                ('shipped_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order'
                )),
                ('product', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL, to='products.product'
                )),
                ('variant', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL, to='products.productvariant'
                )),
                ('seller', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='sold_items', to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['id']},
        ),
        migrations.CreateModel(
            name='OrderStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('from_status', models.CharField(blank=True, max_length=20)),
                ('to_status', models.CharField(max_length=20)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                )),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='status_logs', to='orders.order'
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
