import base64
import pyotp
import qrcode
from io import BytesIO

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from .models import User

@login_required
@require_http_methods(['GET', 'POST'])
def setup_2fa(request):
    """Muestra el QR para configurar 2FA y verifica el primer código."""
    security = request.user.get_or_create_security()
    
    if security.two_factor_enabled:
        messages.info(request, _('La autenticación de dos factores ya está activada.'))
        return redirect('accounts:profile_dashboard')

    if request.method == 'POST':
        # Verificar el código introducido
        code = request.POST.get('code')
        secret = request.session.get('temp_2fa_secret')
        
        if not secret:
            messages.error(request, _('Error en la sesión. Por favor, inténtalo de nuevo.'))
            return redirect('accounts:setup_2fa')
            
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            # Guardar el secreto y activar 2FA
            security.two_factor_enabled = True
            security.two_factor_method = 'totp'
            security.two_factor_secret = secret
            security.save()
            
            # Limpiar sesión
            del request.session['temp_2fa_secret']
            
            messages.success(request, _('¡Autenticación de dos factores activada con éxito!'))
            return redirect('accounts:profile_dashboard')
        else:
            messages.error(request, _('El código introducido es incorrecto. Inténtalo de nuevo.'))

    # Generar un nuevo secreto si no hay uno en sesión o si es GET
    if 'temp_2fa_secret' not in request.session:
        request.session['temp_2fa_secret'] = pyotp.random_base32()
    
    secret = request.session['temp_2fa_secret']
    
    # Generar URL de aprovisionamiento
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=request.user.email, issuer_name="Fenix")
    
    # Generar código QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir imagen a base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'accounts/security/setup_2fa.html', {
        'qr_base64': qr_base64,
        'secret': secret
    })


@require_http_methods(['GET', 'POST'])
def verify_2fa_login(request):
    """Pide el código 2FA durante el login si está activado."""
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('accounts:login')
        
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('accounts:login')
        
    if request.method == 'POST':
        code = request.POST.get('code')
        security = user.get_or_create_security()
        
        if security.two_factor_enabled and security.two_factor_method == 'totp':
            totp = pyotp.TOTP(security.two_factor_secret)
            if totp.verify(code):
                # Código válido, proceder al login
                login(request, user)
                del request.session['pre_2fa_user_id']
                
                next_url = request.GET.get('next') or request.session.get('next_url')
                if next_url:
                    if 'next_url' in request.session:
                        del request.session['next_url']
                    return redirect(next_url)
                return redirect('accounts:dashboard')
            else:
                messages.error(request, _('El código introducido es incorrecto.'))
        else:
            messages.error(request, _('La configuración 2FA de este usuario es inválida.'))
            
    return render(request, 'accounts/security/verify_2fa.html')
