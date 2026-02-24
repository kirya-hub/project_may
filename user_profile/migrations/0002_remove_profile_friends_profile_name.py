from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='friends',
        ),
        migrations.AddField(
            model_name='profile',
            name='name',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Имя'),
        ),
    ]
