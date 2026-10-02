from decimal import Decimal
from django.db import models
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action, throttle_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from apps.core.serializers import *
from apps.businesses.models import Business, Branch, BusinessModule
from apps.catalog.models import Category, Product
from apps.customers.models import Customer
from apps.dining.models import Hall, Table, TableSession
from apps.orders.models import Order, ApprovalRequest
from apps.payments.models import Payment, Refund
from apps.kitchen.models import PreparationStation, KitchenTicket
from apps.inventory.models import IngredientCategory, InventoryItem, StockMovement, RecipeItem
from apps.takeaway.models import PagerDevice, TakeawayProfile
from apps.cashier.models import CashRegister, CashShift, CashMovement, DailyClosing
from apps.cashier.services import close_shift, close_business_day
from apps.suppliers.models import Supplier
from apps.purchasing.models import PurchaseInvoice, PurchaseItem, SupplierPayment
from apps.purchasing.services import post_purchase, create_purchase, pay_supplier
from apps.accounting.models import ExpenseCategory, Expense, FixedOverhead
from apps.accounting.services import create_expense
from apps.reports.services import profit_report
from apps.orders.services import checkout_order, void_order, refund_order, apply_discount
from apps.audit.models import AuditLog
from apps.audit.services import log_action
from apps.accounts.permissions import has_perm
from apps.core.tenancy import tenant_business, require_tenant_business, can_access_branch, assert_branch_access, assert_business_access, assert_related_values_scope, scope_queryset, resolve_branch_for_user
from apps.reports.analytics import sales_analytics
from apps.accounts.models import User
from apps.accounts.permissions import PERMISSION_GROUPS, ALL_PERMISSION_CODES, ROLE_PERMISSIONS
from apps.accounts.override import set_manager_pin, issue_override
from apps.discounts.models import DiscountRule
from apps.discounts.services import find_best_discount
from apps.workforce.models import StaffSchedule, Attendance
from apps.workforce.services import clock_in, clock_out
from apps.inventory.models import WasteRecord
from apps.inventory.services import record_waste
from apps.reports.food_cost import food_cost_report, multi_branch_dashboard
from apps.inventory.models import InventoryCount, InventoryCountLine, StockTransfer, StockTransferLine
from apps.inventory.services import create_inventory_count, post_inventory_count, post_stock_transfer
from apps.production.models import ProductionFormula, ProductionFormulaItem, ProductionBatch
from apps.production.services import post_production_batch
from apps.accounting.models import FiscalSettings
from apps.printing.models import PrinterDevice, PrintTemplate, PrintJob
from apps.printing.services import create_receipt_job, create_kitchen_job, order_receipt_payload, kitchen_ticket_payload
from apps.payments.services import settle_order
from apps.reports.kpi import management_kpis
from django.http import HttpResponse
from apps.inventory.models import InventoryLot
from apps.reservations.models import Reservation
from apps.reservations.services import create_reservation, seat_reservation
from apps.loyalty.models import LoyaltyProgram, CustomerLoyaltyAccount, LoyaltyLedger, WalletAccount, WalletTransaction
from apps.loyalty.services import get_accounts, redeem_points_to_wallet, credit_wallet, earn_order_points
from apps.notifications.models import Notification, SmsProviderConfig
from apps.notifications.services import process_notification, process_pending
from apps.online_ordering.models import OnlineMenuSettings, TableQrToken, OnlineOrder
from apps.online_ordering.services import ensure_settings, public_menu, create_public_order, confirm_online_payment
from apps.online_ordering.throttles import PublicMenuThrottle, OnlineOrderThrottle
from apps.payments.models import BillSplit
from apps.payments.services import create_item_splits, settle_bill_split
from django.http import HttpResponseRedirect
from urllib.parse import quote
from apps.delivery.models import DeliveryZone, DeliveryAddress, CourierProfile, DeliveryAssignment
from apps.delivery.services import delivery_quote, assign_courier, update_delivery_status
from apps.giftcards.models import GiftCard, GiftCardTransaction
from apps.giftcards.services import issue_card, find_card
from apps.payment_gateway.models import PaymentGatewayConfig, GatewayIntent
from apps.payment_gateway.services import create_payment_intent, verify_payment
from apps.loyalty.models import LoyaltyTier, LoyaltyCampaign
from apps.inventory.models import LotInventoryCount, LotInventoryCountLine, InventoryLot
from apps.inventory.services import create_lot_count, post_lot_count
from apps.notifications.models import PushProviderConfig, PushSubscription
from apps.dining.services import get_or_open_table_session, transfer_table_session
from apps.orders.services import transfer_order_items

class BaseVS(viewsets.ModelViewSet):
    """
    Secure-by-default tenant-aware CRUD base.

    Unknown models return an empty queryset for non-platform users.
    Unsafe methods require `cafino_write_permission` on the concrete ViewSet.
    """
    permission_classes=[permissions.IsAuthenticated]
    cafino_read_permission=None
    cafino_write_permission=None
    cafino_allow_destroy=False
    _scope_paths={
        'businesses.business':('pk','pk'),
        'businesses.branch':('pk','business'),
        'businesses.businessmodule':('business','business'),
        'catalog.category':('branch','branch__business'),
        'catalog.product':('branch','branch__business'),
        'customers.customer':('branch','branch__business'),
        'dining.hall':('branch','branch__business'),
        'dining.table':('hall__branch','hall__branch__business'),
        'dining.tablesession':('table__hall__branch','table__hall__branch__business'),
        'orders.order':('branch','branch__business'),
        'kitchen.preparationstation':('branch','branch__business'),
        'kitchen.kitchenticket':('order__branch','order__branch__business'),
        'inventory.ingredientcategory':('branch','branch__business'),
        'inventory.inventoryitem':('branch','branch__business'),
        'inventory.stockmovement':('item__branch','item__branch__business'),
        'inventory.recipeitem':('product__branch','product__branch__business'),
        'inventory.wasterecord':('item__branch','item__branch__business'),
        'inventory.inventorylot':('item__branch','item__branch__business'),
        'takeaway.pagerdevice':('branch','branch__business'),
        'takeaway.takeawayprofile':('order__branch','order__branch__business'),
        'cashier.cashregister':('branch','branch__business'),
        'cashier.cashshift':('register__branch','register__branch__business'),
        'cashier.cashmovement':('shift__register__branch','shift__register__branch__business'),
        'suppliers.supplier':('branch','branch__business'),
        'purchasing.purchaseinvoice':('branch','branch__business'),
        'purchasing.purchaseitem':('invoice__branch','invoice__branch__business'),
        'purchasing.supplierpayment':('supplier__branch','supplier__branch__business'),
        'accounting.expensecategory':('branch','branch__business'),
        'accounting.expense':('branch','branch__business'),
        'accounting.fixedoverhead':('branch','branch__business'),
        'accounting.fiscalsettings':('branch','branch__business'),
        'discounts.discountrule':('branch','branch__business'),
        'workforce.staffschedule':('branch','branch__business'),
        'workforce.attendance':('branch','branch__business'),
        'production.productionformula':('branch','branch__business'),
        'production.productionformulaitem':('formula__branch','formula__branch__business'),
        'production.productionbatch':('branch','branch__business'),
        'printing.printerdevice':('branch','branch__business'),
        'printing.printtemplate':('branch','branch__business'),
        'reservations.reservation':('branch','branch__business'),
        'loyalty.loyaltyprogram':('branch','branch__business'),
        'loyalty.customerloyaltyaccount':('customer__branch','customer__branch__business'),
        'loyalty.walletaccount':('customer__branch','customer__branch__business'),
        'loyalty.loyaltytier':('branch','branch__business'),
        'loyalty.loyaltycampaign':('branch','branch__business'),
        'notifications.notification':('branch','branch__business'),
        'notifications.smsproviderconfig':('branch','branch__business'),
        'notifications.pushproviderconfig':('branch','branch__business'),
        'online_ordering.onlinemenusettings':('branch','branch__business'),
        'online_ordering.tableqrtoken':('table__hall__branch','table__hall__branch__business'),
        'online_ordering.onlineorder':('branch','branch__business'),
        'payments.billsplit':('order__branch','order__branch__business'),
        'delivery.deliveryzone':('branch','branch__business'),
        'delivery.deliveryaddress':('branch','branch__business'),
        'delivery.courierprofile':('branch','branch__business'),
        'payment_gateway.paymentgatewayconfig':('branch','branch__business'),
    }

    def _cross_permission(self,label):
        if label in {'businesses.branch','inventory.inventoryitem'} and has_perm(self.request.user,'inventory.transfer'):
            return 'inventory.transfer'
        return 'branches.dashboard'

    def _has_read_permission(self,user):
        required=self.cafino_read_permission
        if not required:
            return True
        if isinstance(required,str):
            required=(required,)
        return any(has_perm(user,code) for code in required)

    def get_queryset(self):
        qs=super().get_queryset()
        user=self.request.user
        if user.is_superuser:
            return qs
        if not self._has_read_permission(user):
            return qs.none()

        business=tenant_business(user)
        if business is None:
            return qs.none()

        label=qs.model._meta.label_lower
        paths=self._scope_paths.get(label)
        if not paths:
            # A new ViewSet is not tenant-safe until it is explicitly mapped.
            return qs.none()

        own_path,business_path=paths
        if label=='businesses.business':
            return qs.filter(pk=business.pk)

        cross_permission=self._cross_permission(label)
        cross=has_perm(user,cross_permission)

        if label=='businesses.branch':
            if user.branch_id and not cross:
                return qs.filter(pk=user.branch_id)
            return qs.filter(business=business)

        if user.branch_id and not cross:
            return qs.filter(**{own_path:user.branch}).distinct()
        return qs.filter(**{business_path:business}).distinct()

    def _assert_write_permission(self):
        code=self.cafino_write_permission
        if not code or not has_perm(self.request.user,code):
            raise PermissionDenied('دسترسی نوشتن برای این منبع ندارید.')

    def _assert_write_scope(self,validated_data,instance=None):
        user=self.request.user
        if user.is_superuser:
            return
        business=require_tenant_business(user)
        model=getattr(getattr(self,'serializer_class',None),'Meta',None)
        model=getattr(model,'model',None)
        label=model._meta.label_lower if model else ''
        cross_permission=self._cross_permission(label)

        branch=validated_data.get('branch',getattr(instance,'branch',None))
        if branch is not None:
            assert_branch_access(user,branch,cross_permission=cross_permission)

        target_business=validated_data.get('business',getattr(instance,'business',None))
        if target_business is not None:
            assert_business_access(user,target_business)

        assert_related_values_scope(user,validated_data,cross_permission=cross_permission)

    @classmethod
    def _audit_payload(cls,data):
        sensitive=('password','secret','token','api_key','private_key','pin','merchant_id_encrypted','api_key_encrypted','vapid_private_key_encrypted')
        def scrub(value,key=''):
            if key and any(part in key.lower() for part in sensitive):
                return '***'
            if isinstance(value,dict):
                return {str(k):scrub(v,str(k)) for k,v in value.items()}
            if isinstance(value,(list,tuple)):
                return [scrub(v) for v in value]
            return value
        return scrub(dict(data or {}))

    def _log_config_change(self,*,instance,action,before=None,after=None):
        log_action(
            actor=self.request.user,branch=getattr(instance,'branch',None),action=action,
            entity=instance,before=self._audit_payload(before),after=self._audit_payload(after),
            metadata={'model':instance._meta.label_lower,'source':'dashboard-api'},request=self.request
        )

    def perform_create(self,serializer):
        self._assert_write_permission()
        self._assert_write_scope(serializer.validated_data)
        instance=serializer.save()
        self._log_config_change(
            instance=instance,action='CONFIG_CREATED',after=self.get_serializer(instance).data
        )

    def perform_update(self,serializer):
        self._assert_write_permission()
        self._assert_write_scope(serializer.validated_data,serializer.instance)
        before=self.get_serializer(serializer.instance).data
        instance=serializer.save()
        self._log_config_change(
            instance=instance,action='CONFIG_UPDATED',before=before,after=self.get_serializer(instance).data
        )

    def destroy(self,request,*args,**kwargs):
        if not self.cafino_allow_destroy:
            return Response(
                {'detail':'حذف سخت این منبع مجاز نیست؛ از غیرفعال‌سازی/فرآیند دامنه‌ای استفاده کنید'},
                status=405
            )
        self._assert_write_permission()
        return super().destroy(request,*args,**kwargs)

def _branch_accessible(user,branch,*,cross_permission='branches.dashboard'):
    return can_access_branch(user,branch,cross_permission=cross_permission)
