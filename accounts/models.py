from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ROLE_SUPER_ADMIN)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('pending_approval', False)
        extra_fields.setdefault('email_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_MANAGER = 'manager'
    ROLE_CLIENT = 'client'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_CLIENT, 'Client'),
    ]

    LANGUAGE_ES = 'es'
    LANGUAGE_ZH_HANS = 'zh-hans'

    LANGUAGE_CHOICES = [
        (LANGUAGE_ES, 'Español'),
        (LANGUAGE_ZH_HANS, 'Chinese (Simplified)'),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_CLIENT,
    )
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default=LANGUAGE_ES,
    )
    email_verified = models.BooleanField(default=False)
    pending_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS: list[str] = ['full_name']

    def __str__(self) -> str:
        return self.email
