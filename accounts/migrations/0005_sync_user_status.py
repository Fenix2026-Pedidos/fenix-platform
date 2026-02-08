# Generated migration to sync existing user status
from django.db import migrations


def sync_user_status(apps, schema_editor):
    """
    Sincroniza el campo status con el estado real de los usuarios existentes.
    - Si pending_approval=False → status='active'
    - Si pending_approval=True → status='pending'
    - Super admins y staff → status='active'
    """
    User = apps.get_model('accounts', 'User')
    
    for user in User.objects.all():
        # Super admins y staff siempre activos
        if user.is_superuser or user.is_staff or user.role == 'super_admin':
            user.status = 'active'
            user.pending_approval = False
        # Usuarios ya aprobados (pending_approval=False)
        elif not user.pending_approval:
            user.status = 'active'
        # Usuarios inactivos
        elif not user.is_active:
            user.status = 'disabled'
        # Usuarios pendientes (pending_approval=True)
        else:
            user.status = 'pending'
        
        user.save(update_fields=['status', 'pending_approval'])


def reverse_sync(apps, schema_editor):
    """Reversión: volver todos a pending"""
    User = apps.get_model('accounts', 'User')
    User.objects.all().update(status='pending')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_approved_at_user_approved_by_user_status_and_more'),
    ]

    operations = [
        migrations.RunPython(sync_user_status, reverse_sync),
    ]
