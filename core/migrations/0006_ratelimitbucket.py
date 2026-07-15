from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0005_contact_consent_evidence')]

    operations = [
        migrations.CreateModel(
            name='RateLimitBucket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=160, unique=True)),
                ('count', models.PositiveIntegerField(default=0)),
                ('expires_at', models.DateTimeField(db_index=True)),
            ],
            options={'verbose_name': 'Rate limit bucket'},
        )
    ]
