from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('feed', '0004_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedevent',
            name='rarity',
            field=models.CharField(
                choices=[
                    ('COMMON', 'Обычный'),
                    ('RARE', 'Редкий'),
                    ('LEGENDARY', 'Легендарный'),
                ],
                default='COMMON',
                max_length=10,
            ),
        ),
    ]
