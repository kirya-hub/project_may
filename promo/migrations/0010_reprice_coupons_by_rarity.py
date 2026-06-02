from django.db import migrations

PRICES = {
    'COMMON': 500,
    'RARE': 1000,
    'LEGENDARY': 2500,
}


def reprice_forward(apps, schema_editor):
    CouponOffer = apps.get_model('promo', 'CouponOffer')
    for rarity, price in PRICES.items():
        CouponOffer.objects.filter(rarity=rarity).update(cost_points10=price)


def reprice_backward(apps, schema_editor):
    CouponOffer = apps.get_model('promo', 'CouponOffer')
    CouponOffer.objects.all().update(cost_points10=100)


class Migration(migrations.Migration):
    dependencies = [
        ('promo', '0009_couponoffer_title_optional'),
    ]

    operations = [
        migrations.RunPython(reprice_forward, reprice_backward),
    ]
