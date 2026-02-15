from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Order

User = get_user_model()


@override_settings(
    MIDDLEWARE=[
        m for m in [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]
    ]
)
class OrderListViewTests(TestCase):
    """Tests para la vista order_list con separación por roles"""
    
    def setUp(self):
        """Preparar datos de prueba"""
        # Crear usuarios
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            full_name='Cliente Test',
            status='active',
            email_verified=True,
            pending_approval=False
        )
        
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            full_name='Admin Test',
            status='active',
            email_verified=True,
            is_staff=True,
            pending_approval=False
        )
        
        self.other_client = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            full_name='Otro Cliente',
            status='active',
            email_verified=True,
            pending_approval=False
        )
        
        # Crear pedidos
        self.order1 = Order.objects.create(
            customer=self.client_user,
            status=Order.STATUS_NEW,
            total_amount=Decimal('100.00')
        )
        
        self.order2 = Order.objects.create(
            customer=self.client_user,
            status=Order.STATUS_DELIVERED,
            total_amount=Decimal('200.00')
        )
        
        self.order3 = Order.objects.create(
            customer=self.other_client,
            status=Order.STATUS_NEW,
            total_amount=Decimal('150.00')
        )
        
        self.client_http = Client()
    
    def test_client_sees_only_own_orders(self):
        """Cliente solo ve sus propios pedidos"""
        self.client_http.login(email='client@test.com', password='testpass123')
        response = self.client_http.get(reverse('orders:order_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('orders', response.context)
        orders = list(response.context['orders'])
        
        # El cliente debe ver 2 pedidos (suyos)
        self.assertEqual(len(orders), 2)
        self.assertIn(self.order1, orders)
        self.assertIn(self.order2, orders)
        # No debe ver pedido de otro cliente
        self.assertNotIn(self.order3, orders)
        
        # Debe usar el template de lista normal
        self.assertTemplateUsed(response, 'orders/order_list.html')
    
    def test_client_cannot_access_other_client_orders_via_filter(self):
        """Cliente no puede ver pedidos de otros aunque pase filtros en URL"""
        self.client_http.login(email='client@test.com', password='testpass123')
        
        # Intentar acceder con filtros de admin
        response = self.client_http.get(
            reverse('orders:order_list'),
            {'client_id': self.other_client.id, 'month': '2026-02'}
        )
        
        self.assertEqual(response.status_code, 200)
        orders = list(response.context['orders'])
        
        # Debe seguir viendo solo sus pedidos (filtros ignorados)
        self.assertEqual(len(orders), 2)
        self.assertNotIn(self.order3, orders)
    
    def test_admin_sees_aggregated_view(self):
        """Admin ve vista agregada por defecto"""
        self.client_http.login(email='admin@test.com', password='testpass123')
        response = self.client_http.get(reverse('orders:order_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('summary', response.context)
        
        # Debe usar el template de resumen admin
        self.assertTemplateUsed(response, 'orders/orders_admin_summary.html')
    
    def test_admin_can_filter_by_client_and_month(self):
        """Admin puede filtrar por cliente y mes"""
        self.client_http.login(email='admin@test.com', password='testpass123')
        
        # Acceder con filtros de cliente y mes
        response = self.client_http.get(
            reverse('orders:order_list'),
            {
                'client_id': self.client_user.id,
                'month': self.order1.created_at.strftime('%Y-%m')
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('orders', response.context)
        
        # Debe mostrar template de detalle
        self.assertTemplateUsed(response, 'orders/order_list.html')
        self.assertEqual(response.context['view_mode'], 'detail')
    
    def test_unauthenticated_user_redirected(self):
        """Usuario no autenticado es redirigido al login"""
        response = self.client_http.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

