from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import LoginForm, RegisterForm


def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('catalog:product_list')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            if user.is_active and not user.pending_approval:
                login(request, user)
                messages.success(request, f'Bienvenido, {user.full_name}!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('catalog:product_list')
            elif user.pending_approval:
                messages.warning(request, 'Tu cuenta está pendiente de aprobación.')
            else:
                messages.error(request, 'Tu cuenta está desactivada.')
    else:
        form = LoginForm(request)
    
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """Vista de registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('catalog:product_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.pending_approval = True  # Requiere aprobación del manager
            user.email_verified = False
            user.save()
            messages.success(
                request,
                'Registro exitoso. Tu cuenta está pendiente de aprobación por un administrador.'
            )
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    """Vista del perfil del usuario"""
    return render(request, 'accounts/profile.html', {'user': request.user})
