from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('ai_assistant', '0003_ailead')]

    operations = [
        migrations.AlterField(
            model_name='ailead',
            name='otp_code',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='ailead',
            name='otp_last_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ailead',
            name='privacy_accepted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ailead',
            name='privacy_policy_version',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='ailead',
            name='consent_source_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
