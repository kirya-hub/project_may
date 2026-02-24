import django.db.models.constraints
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('promo', '0002_couponoffer'),
        ('user_profile', '0008_promocode_uniq_promocode_profile_offer'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='promocode',
            name='uniq_promocode_profile_offer',
        ),
        migrations.AddConstraint(
            model_name='promocode',
            constraint=models.UniqueConstraint(
                deferrable=django.db.models.constraints.Deferrable['DEFERRED'],
                fields=('profile', 'source_offer'),
                name='uniq_promocode_profile_offer',
            ),
        ),
    ]
