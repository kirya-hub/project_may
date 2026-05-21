from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promo', '0008_add_couponoffer_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='couponoffer',
            name='title',
            field=models.CharField(
                'Название',
                max_length=120,
                blank=True,
                default='',
            ),
        ),
        migrations.AlterField(
            model_name='couponoffer',
            name='description',
            field=models.TextField('Описание'),
        ),
    ]
