from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0005_promocode_rename_user_remove_is_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='promocode',
            options={
                'ordering': ['-acquired_at'],
                'verbose_name': 'Промокод',
                'verbose_name_plural': 'Промокоды',
            },
        ),
    ]
