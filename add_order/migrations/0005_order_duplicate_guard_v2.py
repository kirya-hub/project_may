import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('add_order', '0004_order_duplicate_signature_order_is_duplicate'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='check_dhash',
            field=models.CharField(
                blank=True, db_index=True, default='', max_length=16, verbose_name='dHash чека'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='check_sha256',
            field=models.CharField(
                blank=True, db_index=True, default='', max_length=64, verbose_name='SHA256 чека'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='content_signature',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                max_length=64,
                verbose_name='Сигнатура содержимого',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='duplicate_reason',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Нет'),
                    ('exact_image', 'Точный дубль изображения'),
                    ('image_similar', 'Похожее изображение'),
                    ('content_match', 'Совпадение по содержимому чека'),
                ],
                default='',
                max_length=32,
                verbose_name='Причина дубля',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='duplicate_source_order',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='duplicate_attempts',
                to='add_order.order',
                verbose_name='Исходный заказ-дубль',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='fiscal_number',
            field=models.CharField(
                blank=True, default='', max_length=64, verbose_name='Фискальный номер'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='receipt_date',
            field=models.CharField(blank=True, default='', max_length=32, verbose_name='Дата чека'),
        ),
        migrations.AddField(
            model_name='order',
            name='receipt_number',
            field=models.CharField(
                blank=True, default='', max_length=64, verbose_name='Номер чека'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='receipt_time',
            field=models.CharField(
                blank=True, default='', max_length=32, verbose_name='Время чека'
            ),
        ),
    ]
