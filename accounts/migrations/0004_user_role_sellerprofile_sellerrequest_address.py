from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_phone_number_alter_user_full_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('buyer', 'Buyer'), ('seller', 'Seller')],
                default='buyer', max_length=10
            ),
        ),
        migrations.CreateModel(
            name='SellerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('store_name', models.CharField(max_length=255)),
                ('store_slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('store_logo', models.ImageField(blank=True, null=True, upload_to='sellers/logos/')),
                ('store_banner', models.ImageField(blank=True, null=True, upload_to='sellers/banners/')),
                ('description', models.TextField(blank=True)),
                ('national_id', models.CharField(max_length=50)),
                ('status', models.CharField(
                    choices=[('pending','Pending Review'),('approved','Approved'),('rejected','Rejected'),('suspended','Suspended')],
                    default='pending', max_length=20
                )),
                ('admin_notes', models.TextField(blank=True)),
                ('bank_account', models.CharField(blank=True, max_length=100)),
                ('bank_name', models.CharField(blank=True, max_length=100)),
                ('total_sales', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_orders', models.PositiveIntegerField(default=0)),
                ('rating', models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ('reviews_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='seller_profile', to=settings.AUTH_USER_MODEL
                )),
            ],
        ),
        migrations.CreateModel(
            name='SellerRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('store_name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('national_id', models.CharField(max_length=50)),
                ('phone', models.CharField(max_length=20)),
                ('bank_account', models.CharField(blank=True, max_length=100)),
                ('bank_name', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(
                    choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')],
                    default='pending', max_length=20
                )),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='seller_request', to=settings.AUTH_USER_MODEL
                )),
            ],
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('label', models.CharField(default='Home', max_length=50)),
                ('full_name', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=20)),
                ('address_line1', models.CharField(max_length=255)),
                ('address_line2', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(default='Egypt', max_length=100)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='addresses', to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['-is_default', '-created_at']},
        ),
    ]
