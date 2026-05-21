from django.db import migrations, models
import django.db.models.deletion


def delete_universal_coupons(apps, schema_editor):
    CouponOffer = apps.get_model('promo', 'CouponOffer')
    CouponOffer.objects.filter(cafe__isnull=True).delete()


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('promo', '0006_seed_new_coupons'),
        ('cafes', '0007_city_cafe_city'),
    ]

    operations = [
        migrations.RunPython(delete_universal_coupons, migrations.RunPython.noop),
        migrations.AddField(
            model_name='couponoffer',
            name='menu_item',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='coupon_offers',
                to='cafes.menuitem',
                verbose_name='Блюдо (для фона купона)',
            ),
        ),
        migrations.AlterField(
            model_name='couponoffer',
            name='cafe',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='coupon_offers',
                to='cafes.cafe',
                verbose_name='Кафе',
            ),
        ),
    ]
