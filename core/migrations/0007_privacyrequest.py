import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_ratelimitbucket'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivacyRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('request_type', models.CharField(choices=[('access', 'Acceso/portabilidad'), ('erasure', 'Supresión'), ('rectification', 'Rectificación')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('completed', 'Completada'), ('rejected', 'Rechazada motivadamente')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        )
    ]
