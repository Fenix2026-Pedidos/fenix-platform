# Generated manually for adding image field to Product

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, help_text='Imagen del producto (recomendado: 800x600px)', null=True, upload_to='products/'),
        ),
    ]
