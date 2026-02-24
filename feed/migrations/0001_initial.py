import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('add_order', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Like',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'order',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='likes',
                        to='add_order.order',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='likes',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('user', 'order'), name='unique_like_per_user')
                ],
            },
        ),
    ]
