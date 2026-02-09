"""
URL configuration for fenix project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language

from core.views import global_search, public_about, public_legal, public_privacy

# Personalizar el admin de Django
admin.site.site_header = 'BackOffice Fenix'
admin.site.site_title = 'BackOffice Fenix'
admin.site.index_title = 'Panel de Administración'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/setlang/', set_language, name='set_language'),  # Selector de idioma
    path('api/global-search/', global_search, name='global_search'),
    path('about/', public_about, name='public_about'),
    path('legal/', public_legal, name='public_legal'),
    path('privacy/', public_privacy, name='public_privacy'),
    path('', include('catalog.urls')),
    path('orders/', include('orders.urls')),
    path('accounts/', include('accounts.urls')),
    path('recurring/', include('recurring.urls')),
    path('', include('whatsapp.urls')),  # WhatsApp API endpoints
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
