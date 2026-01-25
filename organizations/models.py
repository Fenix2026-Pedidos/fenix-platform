from django.db import models


class Organization(models.Model):
    LANGUAGE_ES = 'es'
    LANGUAGE_ZH_HANS = 'zh-hans'

    LANGUAGE_CHOICES = [
        (LANGUAGE_ES, 'Español'),
        (LANGUAGE_ZH_HANS, 'Chinese (Simplified)'),
    ]

    name = models.CharField(max_length=200)
    default_language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default=LANGUAGE_ES,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self) -> str:
        return self.name
