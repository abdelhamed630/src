from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from django.conf import settings


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('products', '0003_product_seller'),
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('rating', models.PositiveSmallIntegerField(validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5)
                ])),
                ('title', models.CharField(blank=True, max_length=100)),
                ('body', models.TextField(blank=True)),
                ('seller_reply', models.TextField(blank=True)),
                ('seller_reply_at', models.DateTimeField(blank=True, null=True)),
                ('is_verified_purchase', models.BooleanField(default=False)),
                ('helpful_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='reviews', to='products.product')),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='reviews', to=settings.AUTH_USER_MODEL)),
                ('order_item', models.OneToOneField(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL, to='orders.orderitem')),
            ],
            options={'ordering': ['-created_at'], 'unique_together': {('product', 'buyer')}},
        ),
        migrations.CreateModel(
            name='ReviewHelpful',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='helpful_votes', to='reviews.review')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('review', 'user')}},
        ),
    ]
