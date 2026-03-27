from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_productimage_thumbnail'),
        ('accounts', '0004_user_role_sellerprofile_sellerrequest_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='seller',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products',
                limit_choices_to={'role': 'seller'},
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
