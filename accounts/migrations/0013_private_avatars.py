import core.storage
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0012_protect_security_secrets')]

    operations = [
        migrations.AlterField(
            model_name='user', name='avatar',
            field=models.ImageField(blank=True, null=True, storage=core.storage.private_media_storage, upload_to='avatars/'),
        )
    ]
