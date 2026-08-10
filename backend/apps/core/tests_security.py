from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import connection, close_old_connections
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.businesses.models import Business, Branch
from apps.catalog.models import Category, Product
from apps.inventory.models import IngredientCategory, InventoryItem, RecipeItem, StockMovement, StockTransfer
from apps.orders.models import Order, OrderItem
from apps.orders.services import checkout_order
from apps.purchasing.models import PurchaseInvoice, PurchaseItem
from apps.suppliers.models import Supplier


class TenantSecurityTests(TestCase):
    def setUp(self):
        self.b1=Business.objects.create(name='Tenant A')
        self.b2=Business.objects.create(name='Tenant B')
        self.a1=Branch.objects.create(business=self.b1,name='A1')
        self.a2=Branch.objects.create(business=self.b1,name='A2')
        self.b1_branch=Branch.objects.create(business=self.b2,name='B1')

        self.cashier=User.objects.create_user(
            username='cashier-sec',password='x',business=self.b1,branch=self.a1,role=User.Role.CASHIER
        )
        self.accountant=User.objects.create_user(
            username='accountant-sec',password='x',business=self.b1,branch=self.a1,role=User.Role.ACCOUNTANT
        )
        self.inventory=User.objects.create_user(
            username='inventory-sec',password='x',business=self.b1,branch=self.a1,role=User.Role.INVENTORY
        )
        self.manager=User.objects.create_user(
            username='manager-sec',password='x',business=self.b1,branch=None,role=User.Role.MANAGER
        )
        self.other_manager=User.objects.create_user(
            username='manager-other',password='x',business=self.b2,branch=None,role=User.Role.MANAGER
        )

        self.cat_a1=Category.objects.create(branch=self.a1,name='A1 Category')
        self.cat_a2=Category.objects.create(branch=self.a2,name='A2 Category')
        self.cat_b=Category.objects.create(branch=self.b1_branch,name='B Category')

        self.item_a1=InventoryItem.objects.create(branch=self.a1,name='Beans A1',current_stock=10,average_cost=100)
        self.item_a2=InventoryItem.objects.create(branch=self.a2,name='Beans A2',current_stock=10,average_cost=100)
        self.item_b=InventoryItem.objects.create(branch=self.b1_branch,name='Beans B',current_stock=10,average_cost=100)
        self.supplier_a1=Supplier.objects.create(branch=self.a1,name='Supplier A1')
        self.supplier_a2=Supplier.objects.create(branch=self.a2,name='Supplier A2')
        self.supplier_b=Supplier.objects.create(branch=self.b1_branch,name='Supplier B')

    def client_for(self,user):
        c=APIClient()
        c.force_authenticate(user=user)
        return c

    def test_operational_user_requires_branch(self):
        user=User(username='bad-user',business=self.b1,role=User.Role.CASHIER)
        with self.assertRaises(ValidationError):
            user.save()

    def test_business_level_manager_can_be_branchless_but_not_cross_business(self):
        self.assertIsNone(self.manager.branch_id)
        c=self.client_for(self.manager)
        response=c.get('/api/v1/categories/')
        self.assertEqual(response.status_code,200)
        ids={row['id'] for row in response.json()}
        self.assertEqual(ids,{self.cat_a1.id,self.cat_a2.id})
        self.assertNotIn(self.cat_b.id,ids)

    def test_branch_user_only_reads_own_branch(self):
        c=self.client_for(self.cashier)
        response=c.get('/api/v1/categories/')
        self.assertEqual(response.status_code,200)
        self.assertEqual({row['id'] for row in response.json()},{self.cat_a1.id})

    def test_inventory_user_can_create_a_category_only_for_own_branch(self):
        c=self.client_for(self.inventory)
        response=c.post('/api/v1/categories/',{'branch':self.a1.id,'name':'نوشیدنی سرد'},format='json')
        self.assertEqual(response.status_code,201)
        self.assertTrue(Category.objects.filter(branch=self.a1,name='نوشیدنی سرد').exists())

        duplicate=c.post('/api/v1/categories/',{'branch':self.a1.id,'name':'  نوشیدنی سرد  '},format='json')
        self.assertEqual(duplicate.status_code,400)

        other_business=c.post('/api/v1/categories/',{'branch':self.b1_branch.id,'name':'غیرمجاز'},format='json')
        self.assertEqual(other_business.status_code,403)
        self.assertFalse(Category.objects.filter(branch=self.b1_branch,name='غیرمجاز').exists())

    def test_catalog_delete_requires_no_history_or_configuration_dependencies(self):
        c=self.client_for(self.inventory)
        removable_category=Category.objects.create(branch=self.a1,name='Removable')
        removable_product=Product.objects.create(branch=self.a1,name='Removable product',price=100)

        self.assertEqual(c.delete(f'/api/v1/categories/{removable_category.id}/').status_code,204)
        self.assertEqual(c.delete(f'/api/v1/products/{removable_product.id}/').status_code,204)

        linked_product=Product.objects.create(branch=self.a1,category=self.cat_a1,name='Linked product',price=100)
        category_response=c.delete(f'/api/v1/categories/{self.cat_a1.id}/')
        self.assertEqual(category_response.status_code,400)
        self.assertTrue(Category.objects.filter(pk=self.cat_a1.id).exists())

        order=Order.objects.create(branch=self.a1,order_number=1,order_type=Order.Type.TAKEAWAY)
        OrderItem.objects.create(order=order,product=linked_product,product_name=linked_product.name,quantity=1,unit_price=100,line_total=100)
        product_response=c.delete(f'/api/v1/products/{linked_product.id}/')
        self.assertEqual(product_response.status_code,400)
        self.assertTrue(Product.objects.filter(pk=linked_product.id).exists())

    def test_inventory_material_can_be_used_once_in_same_branch_recipe(self):
        c=self.client_for(self.inventory)
        category_response=c.post('/api/v1/ingredient-categories/',{
            'branch':self.a1.id,'name':'لبنیات','is_active':True,
        },format='json')
        self.assertEqual(category_response.status_code,201)
        category_id=category_response.json()['id']
        material_response=c.post('/api/v1/inventory-items/',{
            'branch':self.a1.id,'name':'شیر تازه','material_category':category_id,'unit':'milliliter',
            'current_stock':'5000','minimum_stock':'1000','average_cost':'20','is_active':True,
        },format='json')
        self.assertEqual(material_response.status_code,201)
        material_id=material_response.json()['id']
        self.assertEqual(material_response.json()['material_category_name'],'لبنیات')
        self.assertEqual(c.delete(f'/api/v1/ingredient-categories/{category_id}/').status_code,400)
        product=Product.objects.create(branch=self.a1,name='لاته',price=100)

        recipe_response=c.post('/api/v1/recipe-items/',{
            'product':product.id,'inventory_item':material_id,'quantity':'200',
        },format='json')
        self.assertEqual(recipe_response.status_code,201)

        duplicate=c.post('/api/v1/recipe-items/',{
            'product':product.id,'inventory_item':material_id,'quantity':'100',
        },format='json')
        self.assertEqual(duplicate.status_code,400)

        cross_branch=c.post('/api/v1/recipe-items/',{
            'product':product.id,'inventory_item':self.item_a2.id,'quantity':'100',
        },format='json')
        self.assertIn(cross_branch.status_code,{400,403,404})

    def test_recipe_editor_saves_multiple_materials_and_updates_them_atomically(self):
        c=self.client_for(self.inventory)
        product=Product.objects.create(branch=self.a1,name='موکا',price=100)
        milk=InventoryItem.objects.create(branch=self.a1,name='شیر',unit='milliliter')
        chocolate=InventoryItem.objects.create(branch=self.a1,name='شکلات',unit='gram')

        created=c.put('/api/v1/recipe-items/save-recipe/',{
            'product':product.id,
            'ingredients':[
                {'inventory_item':milk.id,'quantity':'250'},
                {'inventory_item':chocolate.id,'quantity':'20'},
            ],
        },format='json')
        self.assertEqual(created.status_code,200)
        self.assertEqual(RecipeItem.objects.filter(product=product).count(),2)

        updated=c.put('/api/v1/recipe-items/save-recipe/',{
            'product':product.id,
            'ingredients':[
                {'inventory_item':milk.id,'quantity':'300'},
                {'inventory_item':self.item_a1.id,'quantity':'18'},
            ],
        },format='json')
        self.assertEqual(updated.status_code,200)
        self.assertEqual(RecipeItem.objects.filter(product=product).count(),2)
        self.assertEqual(RecipeItem.objects.get(product=product,inventory_item=milk).quantity,Decimal('300'))
        self.assertFalse(RecipeItem.objects.filter(product=product,inventory_item=chocolate).exists())

        denied=c.put('/api/v1/recipe-items/save-recipe/',{
            'product':product.id,
            'ingredients':[{'inventory_item':self.item_a2.id,'quantity':'1'}],
        },format='json')
        self.assertIn(denied.status_code,{400,403,404})
        self.assertEqual(RecipeItem.objects.filter(product=product).count(),2)


    def test_cashier_cannot_read_purchasing_or_inventory_ledger(self):
        c=self.client_for(self.cashier)
        purchase_response=c.get('/api/v1/purchase-invoices/')
        stock_response=c.get('/api/v1/stock-movements/')
        self.assertEqual(purchase_response.status_code,200)
        self.assertEqual(purchase_response.json(),[])
        self.assertEqual(stock_response.status_code,200)
        self.assertEqual(stock_response.json(),[])

    def test_tenant_manager_cannot_create_another_business(self):
        c=self.client_for(self.manager)
        response=c.post('/api/v1/businesses/',{'name':'Tenant C'},format='json')
        self.assertEqual(response.status_code,403)
        self.assertFalse(Business.objects.filter(name='Tenant C').exists())

    def test_purchase_wrong_supplier_branch_is_denied_without_mutation(self):
        c=self.client_for(self.inventory)
        response=c.post('/api/v1/purchases/create/',{
            'branch':self.a1.id,
            'supplier':self.supplier_a2.id,
            'invoice_date':'2026-08-09',
            'items':[{'inventory_item':self.item_a1.id,'quantity':'2','unit_cost':'100'}],
        },format='json')
        self.assertIn(response.status_code,{400,403,404})
        self.assertEqual(PurchaseInvoice.objects.count(),0)
        self.assertEqual(StockMovement.objects.count(),0)
        self.item_a1.refresh_from_db()
        self.assertEqual(self.item_a1.current_stock,Decimal('10'))

    def test_purchase_wrong_item_branch_is_denied_without_mutation(self):
        c=self.client_for(self.inventory)
        response=c.post('/api/v1/purchases/create/',{
            'branch':self.a1.id,
            'supplier':self.supplier_a1.id,
            'invoice_date':'2026-08-09',
            'items':[{'inventory_item':self.item_a2.id,'quantity':'2','unit_cost':'100'}],
        },format='json')
        self.assertIn(response.status_code,{400,403,404})
        self.assertEqual(PurchaseInvoice.objects.count(),0)
        self.assertEqual(StockMovement.objects.count(),0)

    def test_cross_business_purchase_is_denied(self):
        c=self.client_for(self.inventory)
        response=c.post('/api/v1/purchases/create/',{
            'branch':self.b1_branch.id,
            'supplier':self.supplier_b.id,
            'invoice_date':'2026-08-09',
            'items':[{'inventory_item':self.item_b.id,'quantity':'2','unit_cost':'100'}],
        },format='json')
        self.assertEqual(response.status_code,403)
        self.assertEqual(PurchaseInvoice.objects.count(),0)

    def test_direct_ledger_mutations_are_not_writable(self):
        c=self.client_for(self.inventory)
        stock_response=c.post('/api/v1/stock-movements/',{
            'item':self.item_a1.id,'movement_type':'ADJUSTMENT','quantity':'999'
        },format='json')
        purchase_item_response=c.post('/api/v1/purchase-items/',{
            'invoice':999,'inventory_item':self.item_a1.id,'quantity':'1','unit_cost':'1','line_total':'1'
        },format='json')
        payment_response=c.post('/api/v1/payments/',{'order':999,'amount':'1','method':'CASH'},format='json')
        refund_response=c.post('/api/v1/refunds/',{'payment':999,'amount':'1','reason':'x','method':'CASH'},format='json')

        self.assertEqual(stock_response.status_code,403)
        self.assertEqual(purchase_item_response.status_code,403)
        self.assertEqual(payment_response.status_code,405)
        self.assertEqual(refund_response.status_code,405)
        self.assertEqual(StockMovement.objects.count(),0)
        self.assertEqual(PurchaseItem.objects.count(),0)

    def test_report_cross_branch_denied_for_branch_accountant(self):
        c=self.client_for(self.accountant)
        response=c.get(f'/api/v1/reports/financial/?branch={self.a2.id}')
        self.assertEqual(response.status_code,403)

    def test_report_same_business_cross_branch_allowed_for_business_manager(self):
        c=self.client_for(self.manager)
        response=c.get(f'/api/v1/reports/financial/?branch={self.a2.id}')
        self.assertEqual(response.status_code,200)

    def test_stock_transfer_cannot_cross_business(self):
        c=self.client_for(self.inventory)
        response=c.post('/api/v1/stock-transfers/create/',{
            'source_branch':self.a1.id,
            'destination_branch':self.b1_branch.id,
            'lines':[{
                'source_item':self.item_a1.id,
                'destination_item':self.item_b.id,
                'quantity':'1'
            }]
        },format='json')
        self.assertEqual(response.status_code,400)
        self.assertEqual(StockTransfer.objects.count(),0)


class PostgreSQLCheckoutConcurrencyTests(TransactionTestCase):
    reset_sequences=True

    def setUp(self):
        self.business=Business.objects.create(name='Concurrency')
        self.branch=Branch.objects.create(business=self.business,name='Main')
        self.product=Product.objects.create(branch=self.branch,name='Water',price=1000,is_available=True)

    def _checkout(self,index):
        close_old_connections()
        try:
            branch=Branch.objects.get(pk=self.branch.pk)
            product=Product.objects.get(pk=self.product.pk)
            order=checkout_order(
                branch=branch,
                items=[{'product':product,'quantity':1}],
                order_type=Order.Type.TAKEAWAY,
                defer_payment=True,
                idempotency_key=f'concurrent-{index}',
            )
            return order.order_number
        finally:
            close_old_connections()

    def test_parallel_order_numbers_are_unique_on_postgresql(self):
        if connection.vendor!='postgresql':
            self.skipTest('Row-lock concurrency semantics are verified in PostgreSQL CI.')
        with ThreadPoolExecutor(max_workers=6) as pool:
            numbers=list(pool.map(self._checkout,range(12)))
        self.assertEqual(len(numbers),12)
        self.assertEqual(len(set(numbers)),12)
        self.assertEqual(sorted(numbers),list(range(1,13)))
