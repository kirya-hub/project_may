import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def forwards(apps, schema_editor):
    Profile = apps.get_model('user_profile', 'Profile')
    PointsBalance = apps.get_model('promo', 'PointsBalance')

    for prof in Profile.objects.select_related('user').all():
        PointsBalance.objects.get_or_create(
            user_id=prof.user_id,
            defaults={'points10': prof.points10 or 0},
        )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('promo', '0002_couponoffer'),
        ('user_profile', '0010_remove_promocode_uniq_promocode_profile_offer'),
    ]

    operations = [
        migrations.CreateModel(
            name='PointsBalance',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('points10', models.IntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'user',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='points_balance',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Баланс',
                'verbose_name_plural': 'Балансы',
            },
        ),
        migrations.AddConstraint(
            model_name='pointstransaction',
            constraint=models.UniqueConstraint(
                fields=('order',),
                condition=Q(('kind', 'ACCRUAL')),
                name='uniq_points_accrual_per_order',
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
