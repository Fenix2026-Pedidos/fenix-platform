from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auditlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='platformsettings',
            name='order_notification_email',
            field=models.EmailField(
                blank=True,
                default='',
                help_text='Email que recibe las notificaciones automáticas de pedidos',
                max_length=254,
            ),
        ),
    ]
