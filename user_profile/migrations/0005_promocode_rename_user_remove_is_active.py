from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0004_promocode_status_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='promocode',
            old_name='user',
            new_name='profile',
        ),
        migrations.RemoveField(
            model_name='promocode',
            name='is_active',
        ),
    ]
