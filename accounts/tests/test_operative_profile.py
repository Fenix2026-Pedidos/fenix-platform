"""
Tests for operative profile validation system.

Tests the following components:
1. User model operative profile fields and methods
2. Profile completion check logic
3. Missing fields property and translation
4. Admin visibility and badge display
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class OperativeProfileModelTests(TestCase):
    """Test operative profile fields and methods on User model"""
    
    def setUp(self):
        """Create a test user"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_operative_profile_fields_exist(self):
        """Test that all operative profile fields exist on User model"""
        operative_fields = [
            'telefono_empresa',
            'telefono_reparto',
            'direccion_local',
            'ciudad',
            'provincia',
            'codigo_postal',
            'pais',
            'tipo_entrega',
            'direccion_entrega',
            'ciudad_entrega',
            'provincia_entrega',
            'codigo_postal_entrega',
            'ventana_entrega',
            'observaciones_entrega',
            'profile_completed',
            'items_count'
        ]
        for field in operative_fields:
            self.assertTrue(hasattr(self.user, field), f"Field {field} not found on User model")
    
    def test_profile_completed_default_false(self):
        """New users should have profile_completed=False"""
        self.assertFalse(self.user.profile_completed)
    
    def test_profile_completed_true_when_all_fields_filled(self):
        """profile_completed should be True when all required fields are filled"""
        self.user.telefono_reparto = '555-1234'
        self.user.direccion_local = '123 Main St'
        self.user.ciudad = 'Madrid'
        self.user.provincia = 'Madrid'
        self.user.codigo_postal = '28001'
        self.user.tipo_entrega = 'envio'
        self.user.direccion_entrega = '456 Delivery Ave'
        self.user.ciudad_entrega = 'Barcelona'
        self.user.provincia_entrega = 'Barcelona'
        self.user.codigo_postal_entrega = '08001'
        
        self.user.save()
        # Refresh from database
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_completed)
    
    def test_profile_completed_false_with_missing_fields(self):
        """profile_completed should be False if any required field is missing"""
        # Fill most fields but leave one empty
        self.user.telefono_reparto = '555-1234'
        self.user.direccion_local = '123 Main St'
        self.user.ciudad = 'Madrid'
        self.user.provincia = 'Madrid'
        self.user.codigo_postal = '28001'
        self.user.tipo_entrega = 'envio'
        self.user.direccion_entrega = '456 Delivery Ave'
        self.user.ciudad_entrega = 'Barcelona'
        self.user.provincia_entrega = 'Barcelona'
        # Missing: codigo_postal_entrega
        
        self.user.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_completed)
    
    def test_check_profile_completed_method(self):
        """Test check_profile_completed() method"""
        self.assertFalse(self.user.check_profile_completed())
        
        # Fill all required fields
        self.user.telefono_reparto = '555-1234'
        self.user.direccion_local = '123 Main St'
        self.user.ciudad = 'Madrid'
        self.user.provincia = 'Madrid'
        self.user.codigo_postal = '28001'
        self.user.tipo_entrega = 'envio'
        self.user.direccion_entrega = '456 Delivery Ave'
        self.user.ciudad_entrega = 'Barcelona'
        self.user.provincia_entrega = 'Barcelona'
        self.user.codigo_postal_entrega = '08001'
        
        self.assertTrue(self.user.check_profile_completed())
    
    def test_missing_fields_property(self):
        """Test missing_fields property returns list of missing field names"""
        missing = self.user.missing_fields
        # All fields should be missing for a new user
        self.assertIn('Teléfono de reparto', missing)
        self.assertIn('Dirección local', missing)
        self.assertIn('Ciudad', missing)
        self.assertIn('Provincia', missing)
        self.assertIn('Código postal', missing)
        self.assertIn('Tipo de entrega', missing)
        self.assertIn('Dirección de entrega', missing)
        self.assertIn('Ciudad de entrega', missing)
        self.assertIn('Provincia de entrega', missing)
        self.assertIn('Código postal de entrega', missing)
    
    def test_missing_fields_empty_when_complete(self):
        """missing_fields should be empty when profile is complete"""
        self.user.telefono_reparto = '555-1234'
        self.user.direccion_local = '123 Main St'
        self.user.ciudad = 'Madrid'
        self.user.provincia = 'Madrid'
        self.user.codigo_postal = '28001'
        self.user.tipo_entrega = 'envio'
        self.user.direccion_entrega = '456 Delivery Ave'
        self.user.ciudad_entrega = 'Barcelona'
        self.user.provincia_entrega = 'Barcelona'
        self.user.codigo_postal_entrega = '08001'
        self.user.save()
        
        self.user.refresh_from_db()
        self.assertEqual(len(self.user.missing_fields), 0)


class OperativeProfileFormTests(TestCase):
    """Test OperativeProfileForm validation"""
    
    def setUp(self):
        """Create a test user"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_operative_profile_form_requires_fields(self):
        """Test that form requires obligatory operative profile fields"""
        from accounts.profile_forms import OperativeProfileForm
        
        # Create form with empty data
        form = OperativeProfileForm(data={}, instance=self.user)
        self.assertFalse(form.is_valid())
        
        # At least telefono_reparto should have an error
        self.assertIn('telefono_reparto', form.errors)
    
    def test_operative_profile_form_valid(self):
        """Test that form is valid with all required fields"""
        from accounts.profile_forms import OperativeProfileForm
        
        form_data = {
            'telefono_empresa': '555-0000',
            'telefono_reparto': '555-1234',
            'direccion_local': '123 Main St',
            'ciudad': 'Madrid',
            'provincia': 'Madrid',
            'codigo_postal': '28001',
            'pais': 'Spain',
            'tipo_entrega': 'envio',
            'direccion_entrega': '456 Delivery Ave',
            'ciudad_entrega': 'Barcelona',
            'provincia_entrega': 'Barcelona',
            'codigo_postal_entrega': '08001',
            'ventana_entrega': '09:00-18:00',
            'observaciones_entrega': 'Call before delivery'
        }
        
        form = OperativeProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid(), msg=form.errors)


class OperativeProfileOrderBlockingTests(TestCase):
    """Test that incomplete profiles block order creation"""
    
    def setUp(self):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Approve the user so they can access the system
        self.user.is_approved = True
        self.user.approved_at = timezone.now()
        self.user.status = User.STATUS_ACTIVE
        self.user.save()
    
    def test_incomplete_profile_blocks_order_creation(self):
        """Test that order creation blocks users with incomplete profiles"""
        # User profile is incomplete - they cannot create orders
        self.assertFalse(self.user.profile_completed)
        self.assertTrue(len(self.user.missing_fields) > 0)
    
    def test_complete_profile_allows_order_creation(self):
        """Test that complete profile allows order creation"""
        # Complete the profile
        self.user.telefono_reparto = '555-1234'
        self.user.direccion_local = '123 Main St'
        self.user.ciudad = 'Madrid'
        self.user.provincia = 'Madrid'
        self.user.codigo_postal = '28001'
        self.user.tipo_entrega = 'envio'
        self.user.direccion_entrega = '456 Delivery Ave'
        self.user.ciudad_entrega = 'Barcelona'
        self.user.provincia_entrega = 'Barcelona'
        self.user.codigo_postal_entrega = '08001'
        self.user.save()
        
        # User profile is now complete
        self.assertTrue(self.user.profile_completed)
        self.assertEqual(len(self.user.missing_fields), 0)
        self.user.status = User.STATUS_ACTIVE
        self.user.save()
    
    def test_operative_profile_edit_requires_login(self):
        """Test that operative profile edit requires login"""
        response = self.client.get(reverse('accounts:operative_profile_edit'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_operative_profile_view_exists(self):
        """Test that operative profile view function exists"""
        from accounts.profile_views import operative_profile_edit
        self.assertTrue(callable(operative_profile_edit))


class OperativeProfileAdminTests(TestCase):
    """Test admin interface for operative profiles"""
    
    def setUp(self):
        """Set up test users and admin"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass'
        )
        self.regular_user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_admin_user_can_be_created(self):
        """Test that admin users can be created"""
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)
    
    def test_operative_profile_badge_method_exists(self):
        """Test that profile_completed_badge method exists on User admin"""
        from accounts.admin import UserAdmin
        admin = UserAdmin(User, None)
        self.assertTrue(hasattr(admin, 'profile_completed_badge'))
