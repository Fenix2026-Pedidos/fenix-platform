import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'fenix.settings'
import django
django.setup()
from accounts.models import User

# Create temp test user or reset password for testing
email = 'testadmin@fenix.local'
try:
    u = User.objects.get(email=email)
    u.set_password('Test1234!')
    u.save()
    print(f"Updated password for {email}")
except User.DoesNotExist:
    u = User.objects.create_user(
        email=email,
        password='Test1234!',
        full_name='Test Admin',
        is_staff=True,
        is_active=True,
        role='admin',
        status='active',
        email_verified=True,
        pending_approval=False,
    )
    print(f"Created user {email}")
print("Credentials: testadmin@fenix.local / Test1234!")
