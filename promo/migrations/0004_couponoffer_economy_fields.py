from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('promo', '0003_pointsbalance_and_antabuse'),
    ]

    operations = [
        migrations.AddField(
            model_name='couponoffer',
            name='available_in_drop',
            field=models.BooleanField(default=True, verbose_name='Доступен в Drop'),
        ),
        migrations.AddField(
            model_name='couponoffer',
            name='available_in_shop',
            field=models.BooleanField(default=True, verbose_name='Доступен в магазине'),
        ),
        migrations.AddField(
            model_name='couponoffer',
            name='rarity',
            field=models.CharField(
                choices=[
                    ('COMMON', 'Обычный'),
                    ('RARE', 'Редкий'),
                    ('LEGENDARY', 'Легендарный'),
                ],
                default='COMMON',
                max_length=12,
                verbose_name='Редкость',
            ),
        ),
        migrations.AddField(
            model_name='couponoffer',
            name='reward_type',
            field=models.CharField(
                choices=[
                    ('COFFEE', 'Кофе'),
                    ('DESSERT', 'Десерт'),
                    ('DISCOUNT', 'Скидка'),
                    ('DRINK', 'Напиток'),
                    ('MEAL', 'Еда'),
                    ('COMBO', 'Комбо'),
                ],
                default='DISCOUNT',
                max_length=20,
                verbose_name='Тип награды',
            ),
        ),
        migrations.AddIndex(
            model_name='couponoffer',
            index=models.Index(
                fields=['is_active', 'available_in_shop', 'reward_type', 'rarity'],
                name='promo_coupo_is_acti_34e10a_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='couponoffer',
            index=models.Index(
                fields=['is_active', 'available_in_drop', 'rarity'],
                name='promo_coupo_is_acti_6cb3b5_idx',
            ),
        ),
    ]
