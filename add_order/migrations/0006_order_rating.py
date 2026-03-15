from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('add_order', '0005_order_duplicate_guard_v2'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='rating',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[MinValueValidator(1), MaxValueValidator(5)],
                verbose_name='Оценка',
            ),
        ),
    ]
