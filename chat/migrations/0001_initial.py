from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('buyer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='buyer_conversations', to=settings.AUTH_USER_MODEL
                )),
                ('seller', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='seller_conversations', to=settings.AUTH_USER_MODEL
                )),
                ('order', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='conversations', to='orders.order'
                )),
            ],
            options={
                'ordering': ['-updated_at'],
                'unique_together': {('buyer', 'seller', 'order')},
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('attachment', models.FileField(blank=True, null=True, upload_to='chat/attachments/')),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages', to='chat.conversation'
                )),
                ('sender', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sent_messages', to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['created_at']},
        ),
    ]
