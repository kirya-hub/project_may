import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('cafes', '0003_menucategory_slug'),
        ('promo', '0002_couponoffer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DropOption',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'rarity',
                    models.CharField(
                        choices=[
                            ('COMMON', 'Обычный'),
                            ('RARE', 'Редкий'),
                            ('LEGENDARY', 'Легендарный'),
                        ],
                        default='COMMON',
                        max_length=10,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'cafe',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='drop_options',
                        to='cafes.cafe',
                    ),
                ),
                (
                    'reward_offer',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='drop_rewards',
                        to='promo.couponoffer',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='DropWeek',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('week_start', models.DateField()),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('CHOOSING', 'Выбор'),
                            ('ACTIVE', 'Активен'),
                            ('COMPLETED', 'Завершён'),
                            ('EXPIRED', 'Истёк'),
                        ],
                        default='CHOOSING',
                        max_length=12,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'chosen_option',
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='chosen_in_week',
                        to='drops.dropoption',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='drop_weeks',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='dropoption',
            name='drop_week',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='options',
                to='drops.dropweek',
            ),
        ),
        migrations.AddConstraint(
            model_name='dropweek',
            constraint=models.UniqueConstraint(
                fields=('user', 'week_start'), name='uniq_dropweek_user_week'
            ),
        ),
    ]
