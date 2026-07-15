from django.db import migrations, models


def revoke_exposed_security_material(apps, schema_editor):
    SecuritySettings = apps.get_model('accounts', 'SecuritySettings')
    UserSession = apps.get_model('accounts', 'UserSession')
    Session = apps.get_model('sessions', 'Session')
    SecuritySettings.objects.update(
        two_factor_enabled=False,
        two_factor_method='',
        two_factor_secret='',
        api_token=None,
        api_token_created_at=None,
        api_token_last_used=None,
    )
    UserSession.objects.all().delete()
    Session.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0011_user_job_title_user_vat_number'),
        ('sessions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securitysettings', name='two_factor_secret',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='securitysettings', name='api_token',
            field=models.CharField(blank=True, default=None, max_length=128, null=True, unique=True),
        ),
        migrations.RunPython(revoke_exposed_security_material, migrations.RunPython.noop),
    ]
