# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='stock_deducted',
            field=models.BooleanField(
                default=False,
                help_text='True cuando el stock se ha descontado al pasar a Preparando',
            ),
        ),
    ]
