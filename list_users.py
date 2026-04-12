import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'fenix.settings'
import django
django.setup()
from accounts.models import User
users = User.objects.all()
for u in users[:10]:
    print(f"{u.email} | active={u.is_active} | staff={u.is_staff} | status={u.status} | role={u.role}")
