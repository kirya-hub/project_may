import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('cafes', '0003_menucategory_slug'),
        ('feed', '0002_alter_like_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedEvent',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('kind', models.CharField(choices=[('DROP_CHOSEN', 'Выбор Drop')], max_length=20)),
                ('text', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'cafe',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='feed_events',
                        to='cafes.cafe',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='feed_events',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
