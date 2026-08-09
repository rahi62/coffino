from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.accounts.models import User
from apps.accounts.override import set_manager_pin, issue_override, validate_override
class ManagerOverrideTests(TestCase):
    def test_pin_issues_scoped_token(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        u=User.objects.create_user(username='m',password='x',branch=br,role='MANAGER')
        set_manager_pin(u,'4321')
        token,manager=issue_override(branch=br,pin='4321',permission_code='discount.manual')
        self.assertEqual(manager,u)
        self.assertEqual(validate_override(token,branch=br,permission_code='discount.manual'),u)
        self.assertIsNone(validate_override(token,branch=br,permission_code='orders.void'))
