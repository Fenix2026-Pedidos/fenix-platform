import sys
from django.contrib.auth import get_user_model
User = get_user_model()

print("\n=== USUARIOS EN FENIX ===")
for u in User.objects.all()[:10]:
    role = getattr(u, 'role', 'N/A')
    status = getattr(u, 'status', 'N/A')
    print(f"[{u.id}] Email: {u.email}")
    print(f"      Nombre: {u.first_name} {u.last_name}")
    print(f"      Rol: {role} | Status: {status}")
    print(f"      Superuser: {u.is_superuser} | Staff: {u.is_staff} | Active: {u.is_active}")
    print(f"      Permisos directos: {[p.codename for p in u.user_permissions.all()][:5]}...")
    print("-" * 50)
print("=========================\n")
