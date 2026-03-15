from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('cafes', '0004_cafestaff_cafe_working_hours_cafe_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='cafe',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='cafe',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]
