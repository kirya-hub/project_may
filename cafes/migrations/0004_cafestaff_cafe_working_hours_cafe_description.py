import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cafes', '0003_menucategory_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='cafe',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='cafe',
            name='working_hours',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.CreateModel(
            name='CafeStaff',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'cafe',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='staff_members',
                        to='cafes.cafe',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='cafe_staff_links',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Сотрудник кафе',
                'verbose_name_plural': 'Сотрудники кафе',
                'unique_together': {('cafe', 'user')},
            },
        ),
    ]
