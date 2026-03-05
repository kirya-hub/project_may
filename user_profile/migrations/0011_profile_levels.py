from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0010_remove_promocode_uniq_promocode_profile_offer'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='level',
            field=models.PositiveIntegerField(default=1, verbose_name='Уровень'),
        ),
        migrations.AddField(
            model_name='profile',
            name='xp',
            field=models.PositiveIntegerField(default=0, verbose_name='Опыт'),
        ),
        migrations.AddField(
            model_name='profile',
            name='last_trade_xp_date',
            field=models.DateField(
                blank=True, null=True, verbose_name='Дата последнего XP за обмен'
            ),
        ),
    ]
