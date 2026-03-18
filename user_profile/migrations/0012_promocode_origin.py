from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0011_profile_levels'),
    ]

    operations = [
        migrations.AddField(
            model_name='promocode',
            name='origin',
            field=models.CharField(
                choices=[('SHOP', 'Магазин'), ('DROP', 'Drop')],
                default='SHOP',
                max_length=10,
                verbose_name='Источник',
            ),
        ),
    ]
