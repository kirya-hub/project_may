from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('add_order', '0002_order_cafe'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='points_accrued',
            field=models.BooleanField(default=False),
        ),
    ]
