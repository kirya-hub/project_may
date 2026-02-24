import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('user_profile', '0008_promocode_uniq_promocode_profile_offer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TradeOffer',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('PENDING', 'Ожидает ответа'),
                            ('ACCEPTED', 'Принят'),
                            ('DECLINED', 'Отклонён'),
                            ('CANCELLED', 'Отменён'),
                        ],
                        default='PENDING',
                        max_length=12,
                    ),
                ),
                ('message', models.CharField(blank=True, default='', max_length=240)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                (
                    'from_user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='trade_offers_sent',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'to_user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='trade_offers_received',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TradeItem',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'side',
                    models.CharField(
                        choices=[('OFFERED', 'Отдаю'), ('REQUESTED', 'Хочу')], max_length=10
                    ),
                ),
                (
                    'promocode',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='trade_items',
                        to='user_profile.promocode',
                    ),
                ),
                (
                    'trade',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='items',
                        to='trades.tradeoffer',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='TradeActivity',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'kind',
                    models.CharField(
                        choices=[
                            ('CREATED', 'Создано предложение'),
                            ('ACCEPTED', 'Обмен принят'),
                            ('DECLINED', 'Обмен отклонён'),
                            ('CANCELLED', 'Обмен отменён'),
                        ],
                        max_length=10,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'actor',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='trade_activities',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'trade',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='activities',
                        to='trades.tradeoffer',
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='tradeoffer',
            index=models.Index(
                fields=['to_user', 'status', '-created_at'], name='trades_trad_to_user_b8f38a_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='tradeoffer',
            index=models.Index(
                fields=['from_user', 'status', '-created_at'], name='trades_trad_from_us_d1f914_idx'
            ),
        ),
        migrations.AddConstraint(
            model_name='tradeitem',
            constraint=models.UniqueConstraint(
                fields=('trade', 'promocode'), name='uniq_trade_promocode'
            ),
        ),
        migrations.AddIndex(
            model_name='tradeactivity',
            index=models.Index(fields=['-created_at'], name='trades_trad_created_f29c33_idx'),
        ),
        migrations.AddIndex(
            model_name='tradeactivity',
            index=models.Index(fields=['kind', '-created_at'], name='trades_trad_kind_b7c6f9_idx'),
        ),
    ]
