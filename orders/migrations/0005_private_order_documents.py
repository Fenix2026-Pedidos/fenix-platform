import core.storage
import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0004_alter_order_options_alter_orderevent_options_and_more')]

    operations = [
        migrations.AlterField(
            model_name='orderdocument',
            name='file',
            field=models.FileField(
                storage=core.storage.private_order_storage,
                upload_to='order_documents/%Y/%m/',
                validators=[core.validators.validate_private_document],
                verbose_name='Archivo',
            ),
        )
    ]
