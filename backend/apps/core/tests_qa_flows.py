from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.businesses.models import Business,Branch,BusinessModule
from apps.catalog.models import Category,Product
from apps.accounts.permissions import has_perm

class QaCheckoutMenuTests(TestCase):
    def setUp(self):
        self.business=Business.objects.create(name="QA cafe")
        self.branch=Branch.objects.create(business=self.business,name="QA branch")
        self.other=Business.objects.create(name="Foreign cafe")
        self.foreign=Branch.objects.create(business=self.other,name="Foreign branch")
        BusinessModule.objects.create(business=self.business,key="POS",enabled=True)
        BusinessModule.objects.create(business=self.business,key="INVENTORY",enabled=False)
        BusinessModule.objects.create(business=self.business,key="NOTIFICATIONS",enabled=False)
        self.owner=User.objects.create_user(username="qa-owner",password="test",business=self.business,branch=self.branch,role="OWNER")
        self.manager=User.objects.create_user(username="qa-manager",password="test",business=self.business,branch=self.branch,role="MANAGER")
        self.cashier=User.objects.create_user(username="qa-cashier",password="test",business=self.business,branch=self.branch,role="CASHIER")
    def client_as(self,user):
        c=APIClient();c.force_authenticate(user=user);return c
    def test_catalog_write_independent_of_inventory(self):
        for user in (self.owner,self.manager,self.cashier):
            self.assertTrue(has_perm(user,"catalog.manage"))
            self.assertFalse(has_perm(user,"inventory.manage"))
            c=self.client_as(user)
            category=c.post("/api/v1/categories/",{"branch":self.branch.pk,"name":"Coffee"},format="json")
            self.assertEqual(category.status_code,201,category.content)
            product=c.post("/api/v1/products/",{"branch":self.branch.pk,"name":"Latte","price":1000,"category":category.json()["id"]},format="json")
            self.assertEqual(product.status_code,201,product.content)
            self.assertEqual(c.get("/api/v1/categories/").status_code,200)
            self.assertIn(category.json()["id"],[row["id"] for row in c.get("/api/v1/categories/").json()])
            self.assertEqual(c.patch(f'/api/v1/categories/{category.json()["id"]}/',{"name":"Updated"},format="json").status_code,200)
    def test_override_and_tenant_cannot_write(self):
        self.cashier.permission_overrides={"catalog.manage":False}
        self.cashier.save(update_fields=["permission_overrides"])
        c=self.client_as(self.cashier)
        self.assertEqual(c.post("/api/v1/categories/",{"branch":self.branch.pk,"name":"No"},format="json").status_code,403)
        c=self.client_as(self.owner)
        self.assertIn(c.post("/api/v1/categories/",{"branch":self.foreign.pk,"name":"Foreign"},format="json").status_code,(400,403))
    def test_checkout_notification_rejects_disabled_channels_without_order(self):
        c=self.client_as(self.owner)
        product=Product.objects.create(branch=self.branch,name="Tea",price=200)
        payload={"branch":self.branch.pk,"items":[{"product":product.pk,"quantity":1}],"order_type":"TAKEAWAY","payments":[{"method":"POS","amount":"200"}],"ready_notification_method":"SMS","customer_phone":"09123456789"}
        self.assertEqual(c.get(f"/api/v1/checkout-notification-options/?branch={self.branch.pk}").json(),{"sms":False,"pager":False})
        self.assertEqual(c.post("/api/v1/checkout/",payload,format="json").status_code,400)
        payload["ready_notification_method"]="PAGER"
        self.assertEqual(c.post("/api/v1/checkout/",payload,format="json").status_code,400)
    def test_branchless_owner_must_select_authorized_branch_after_second_branch(self):
        owner=User.objects.create_user(username="qa-unassigned",password="test",business=self.business,role="OWNER")
        second=Branch.objects.create(business=self.business,name="Second")
        c=self.client_as(owner)
        self.assertEqual(c.get("/api/v1/dashboard/").status_code,403)
        self.assertEqual(c.get(f"/api/v1/dashboard/?branch={self.foreign.pk}").status_code,403)
