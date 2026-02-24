from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('cafes', '0002_menuitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='menucategory',
            name='slug',
            field=models.SlugField(blank=True, unique=True),
        ),
    ]
