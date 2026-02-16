from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import profile_views

app_name = 'accounts'

urlpatterns = [
    # Dashboard/Inicio
    path('inicio/', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),  # Alias
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Nuevo módulo de perfil enterprise (Dashboard completo)
    path('profile/', profile_views.profile_dashboard, name='profile'),  # Nueva vista principal
    path('profile/dashboard/', profile_views.profile_dashboard, name='profile_dashboard'),  # Alias
    path('profile/edit/', profile_views.update_complete_profile, name='update_complete_profile'),
    path('profile/personal/edit/', profile_views.update_personal_data, name='update_personal_data'),
    path('profile/company/edit/', profile_views.update_company_data, name='update_company_data'),
    path('profile/operative/edit/', profile_views.update_operative_profile, name='update_operative_profile'),
    path('profile/preferences/edit/', profile_views.update_preferences, name='update_preferences'),
    path('profile/security/edit/', profile_views.update_security, name='update_security'),
    path('profile/password/change/', profile_views.change_password, name='change_password'),
    path('profile/2fa/enable/', profile_views.enable_2fa, name='enable_2fa'),
    path('profile/2fa/disable/', profile_views.disable_2fa, name='disable_2fa'),
    path('profile/sessions/', profile_views.active_sessions, name='active_sessions'),
    path('profile/sessions/<int:session_id>/revoke/', profile_views.revoke_session, name='revoke_session'),
    path('profile/sessions/revoke-all/', profile_views.revoke_all_sessions, name='revoke_all_sessions'),
    path('profile/avatar/upload/', profile_views.upload_avatar, name='upload_avatar'),
    path('profile/avatar/delete/', profile_views.delete_avatar, name='delete_avatar'),
    path('profile/login-history/', profile_views.login_history, name='login_history'),
    path('profile/audit-log/', profile_views.audit_log, name='audit_log'),
    path('profile/api-token/generate/', profile_views.generate_api_token, name='generate_api_token'),
    path('profile/api-token/revoke/', profile_views.revoke_api_token, name='revoke_api_token'),
    
    # Administración de perfiles de otros usuarios (Solo ADMIN/SUPER_ADMIN)
    path('profile/<int:user_id>/', profile_views.admin_view_user_profile, name='admin_view_user'),
    path('profile/<int:user_id>/edit/', profile_views.admin_edit_user_profile, name='admin_edit_user'),
    
    # Perfil operativo (requerido para crear pedidos)
    path('operative-profile/edit/', profile_views.operative_profile_edit, name='operative_profile_edit'),
    
    # User approval dashboard (nuevo)
    path('user-approval/', views.user_approval_list, name='user_approval_dashboard'),
    path('approval/', views.user_approval_list, name='user_approval_list'),  # Alias por compatibilidad con URL vieja
    
    # CRUD de usuarios
    path('user-approval/users/<int:user_id>/update/', views.user_update_view, name='user_update'),
    path('user-approval/users/<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
    
    # Aprobación/rechazo de nuevos usuarios
    path('user-approval/new/<int:user_id>/approve/', views.approve_user_view, name='approve_user'),
    path('user-approval/new/<int:user_id>/reject/', views.reject_user_view, name='reject_user'),
    path('user-approval/request/update/', views.update_pending_request, name='update_pending_request'),
    
    # Email verification
    path('email-verification/', views.email_verification_view, name='email_verification'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-confirmation/', views.resend_confirmation, name='resend_confirmation'),
    
    # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset_form.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
