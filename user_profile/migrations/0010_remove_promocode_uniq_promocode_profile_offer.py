from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0009_remove_promocode_uniq_promocode_profile_offer_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='promocode',
            name='uniq_promocode_profile_offer',
        ),
    ]
