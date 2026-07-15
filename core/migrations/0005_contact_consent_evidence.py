from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0004_contactlead')]

    operations = [
        migrations.AddField(model_name='contactlead', name='privacy_accepted_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='contactlead', name='privacy_policy_version', field=models.CharField(blank=True, max_length=32)),
        migrations.AddField(model_name='contactlead', name='marketing_consent_at', field=models.DateTimeField(blank=True, null=True)),
    ]
