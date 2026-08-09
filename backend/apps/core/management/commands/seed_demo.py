from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.businesses.models import Business, Branch, BusinessModule
from apps.catalog.models import Category, Product
from apps.customers.models import Customer
from apps.kitchen.models import PreparationStation
from apps.dining.models import Hall, Table
from apps.inventory.models import InventoryItem, RecipeItem, InventoryLot
from apps.cashier.models import CashRegister
from apps.suppliers.models import Supplier
from apps.accounting.models import ExpenseCategory, FixedOverhead, FiscalSettings
from apps.takeaway.models import PagerDevice
from apps.accounts.models import User
from apps.accounts.override import set_manager_pin
from apps.discounts.models import DiscountRule
from apps.production.models import ProductionFormula, ProductionFormulaItem
from apps.loyalty.models import LoyaltyProgram
from apps.loyalty.services import credit_wallet,get_accounts
from apps.online_ordering.services import ensure_settings
from apps.online_ordering.models import TableQrToken
from apps.notifications.models import SmsProviderConfig
from apps.delivery.models import DeliveryZone,CourierProfile
from apps.payment_gateway.models import PaymentGatewayConfig
from apps.loyalty.models import LoyaltyTier,LoyaltyCampaign

class Command(BaseCommand):
    help="Seed demo Cafino data"
    def handle(self,*args,**kwargs):
        b,_=Business.objects.get_or_create(name="کافینو دمو")
        br,_=Branch.objects.get_or_create(business=b,name="شعبه اصلی")
        second,_=Branch.objects.get_or_create(business=b,name="شعبه دوم")
        for key in ["CORE","POS","DINE_IN","TAKEAWAY","KITCHEN_DISPLAY","PAGER","SMS","INVENTORY","RECIPES","PURCHASING","ACCOUNTING","CUSTOMERS","REPORTING","PRODUCTION","PRINTING","MULTI_BRANCH","RESERVATION","LOYALTY","ONLINE_ORDERING","NOTIFICATIONS","DELIVERY","GIFT_CARD","PAYMENT_GATEWAY"]:
            BusinessModule.objects.get_or_create(business=b,key=key)
        coffee,_=PreparationStation.objects.get_or_create(branch=br,code="COFFEE_BAR",defaults={"name":"بار قهوه"})
        kitchen,_=PreparationStation.objects.get_or_create(branch=br,code="KITCHEN",defaults={"name":"آشپزخانه"})
        c1,_=Category.objects.get_or_create(branch=br,name="قهوه"); c2,_=Category.objects.get_or_create(branch=br,name="کیک و دسر")
        latte,_=Product.objects.get_or_create(branch=br,name="لاته",defaults={"category":c1,"price":1500000,"preparation_station":coffee})
        americano,_=Product.objects.get_or_create(branch=br,name="آمریکانو",defaults={"category":c1,"price":1200000,"preparation_station":coffee})
        Product.objects.get_or_create(branch=br,name="چیزکیک",defaults={"category":c2,"price":1800000,"preparation_station":kitchen})
        Customer.objects.get_or_create(branch=br,name="مشتری گذری",is_walk_in=True)
        vip,_=Customer.objects.get_or_create(branch=br,phone="09121111111",defaults={"name":"مشتری وفادار","is_walk_in":False})
        hall,_=Hall.objects.get_or_create(branch=br,name="سالن اصلی")
        for n in range(1,9): Table.objects.get_or_create(hall=hall,number=str(n),defaults={"capacity":4})
        beans,_=InventoryItem.objects.get_or_create(branch=br,name="دانه قهوه",defaults={"unit":"gram","current_stock":5000,"minimum_stock":1000,"average_cost":1200})
        milk,_=InventoryItem.objects.get_or_create(branch=br,name="شیر",defaults={"unit":"ml","current_stock":12000,"minimum_stock":3000,"average_cost":500})
        beans.item_code="BEANS";beans.save(update_fields=["item_code"])
        milk.item_code="MILK";milk.save(update_fields=["item_code"])
        InventoryItem.objects.get_or_create(branch=second,name="دانه قهوه",defaults={"item_code":"BEANS","unit":"gram","current_stock":1000,"minimum_stock":500,"average_cost":1200})
        InventoryItem.objects.get_or_create(branch=second,name="شیر",defaults={"item_code":"MILK","unit":"ml","current_stock":3000,"minimum_stock":1000,"average_cost":500})
        flour,_=InventoryItem.objects.get_or_create(branch=br,name="آرد",defaults={"item_code":"FLOUR","unit":"gram","current_stock":20000,"minimum_stock":3000,"average_cost":100})
        cocoa,_=InventoryItem.objects.get_or_create(branch=br,name="پودر کاکائو",defaults={"item_code":"COCOA","unit":"gram","current_stock":5000,"minimum_stock":500,"average_cost":400})
        brownie_stock,_=InventoryItem.objects.get_or_create(branch=br,name="براونی آماده",defaults={"item_code":"BROWNIE-FG","unit":"piece","current_stock":0,"minimum_stock":5,"average_cost":0,"lot_tracked":True,"shelf_life_days":5})
        if not brownie_stock.lot_tracked:brownie_stock.lot_tracked=True;brownie_stock.shelf_life_days=5;brownie_stock.save(update_fields=["lot_tracked","shelf_life_days"])
        brownie_product,_=Product.objects.get_or_create(branch=br,name="براونی",defaults={"category":c2,"price":1600000,"product_type":"PACKAGED_ITEM","stock_item":brownie_stock})
        if brownie_product.stock_item_id!=brownie_stock.id:
            brownie_product.stock_item=brownie_stock;brownie_product.product_type="PACKAGED_ITEM";brownie_product.save(update_fields=["stock_item","product_type"])
        formula,_=ProductionFormula.objects.get_or_create(branch=br,name="Batch براونی 20 عدد",defaults={"output_item":brownie_stock,"output_quantity":20})
        ProductionFormulaItem.objects.get_or_create(formula=formula,inventory_item=flour,defaults={"quantity":1000})
        ProductionFormulaItem.objects.get_or_create(formula=formula,inventory_item=cocoa,defaults={"quantity":300})

        RecipeItem.objects.get_or_create(product=latte,inventory_item=beans,defaults={"quantity":18}); RecipeItem.objects.get_or_create(product=latte,inventory_item=milk,defaults={"quantity":250}); RecipeItem.objects.get_or_create(product=americano,inventory_item=beans,defaults={"quantity":18})
        for n in range(1,11): PagerDevice.objects.get_or_create(branch=br,number=str(n))
        CashRegister.objects.get_or_create(branch=br,name="صندوق اصلی")
        Supplier.objects.get_or_create(branch=br,name="تامین قهوه مرکزی",defaults={"phone":"09120000000"})
        ExpenseCategory.objects.get_or_create(branch=br,name="حمل و نقل")
        ExpenseCategory.objects.get_or_create(branch=br,name="تعمیر و نگهداری")
        FixedOverhead.objects.get_or_create(branch=br,title="اجاره ماهانه",defaults={"amount":100000000,"frequency":"MONTHLY","is_active":True})
        FiscalSettings.objects.get_or_create(branch=br,defaults={"tax_enabled":False,"tax_rate":0,"service_charge_enabled":True,"service_charge_rate":10,"service_charge_order_types":["DINE_IN"]})
        FiscalSettings.objects.get_or_create(branch=second,defaults={"tax_enabled":False,"tax_rate":0,"service_charge_enabled":True,"service_charge_rate":10,"service_charge_order_types":["DINE_IN"]})
        LoyaltyProgram.objects.get_or_create(branch=br,defaults={"is_active":True,"amount_per_point":100000,"point_wallet_value":10000,"min_redeem_points":10})
        loyalty_account,wallet=get_accounts(vip)
        if wallet.balance==0:credit_wallet(vip,500000,reference="SEED",note="اعتبار دمو")
        online=ensure_settings(br);online.is_enabled=True;online.accepting_orders=True;online.payment_mode="PAY_AT_COUNTER";online.welcome_text="به منوی آنلاین کافینو خوش آمدید";online.save()
        for table in hall.tables.all():TableQrToken.objects.get_or_create(table=table)
        SmsProviderConfig.objects.get_or_create(branch=br,defaults={"provider_name":"GENERIC_HTTP","is_active":False})
        DeliveryZone.objects.get_or_create(branch=br,code="NEAR",defaults={"name":"محدوده نزدیک","delivery_fee":300000,"min_order_amount":1000000,"free_delivery_above":8000000,"estimated_minutes":25})
        CourierProfile.objects.get_or_create(branch=br,name="پیک دمو",defaults={"phone":"09122222222","vehicle":"موتور","status":"AVAILABLE","is_active":True})
        PaymentGatewayConfig.objects.get_or_create(branch=br,defaults={"provider":"MOCK","is_active":True,"callback_base_url":"http://127.0.0.1:8000"})
        LoyaltyTier.objects.get_or_create(branch=br,code="GOLD",defaults={"name":"طلایی","min_lifetime_points":100,"points_multiplier":1.5,"is_active":True})
        u,created=User.objects.get_or_create(username="admin",defaults={"branch":br,"role":"OWNER","is_staff":True,"is_superuser":True})
        if created or not u.check_password("admin1234"):
            u.set_password("admin1234"); u.branch=br; u.role="OWNER"; u.is_staff=True; u.is_superuser=True; u.save()
        set_manager_pin(u,"4321")
        cashier,c_created=User.objects.get_or_create(username="cashier",defaults={"branch":br,"role":"CASHIER","first_name":"صندوق‌دار"})
        if c_created or not cashier.check_password("cashier1234"):
            cashier.set_password("cashier1234");cashier.branch=br;cashier.role="CASHIER";cashier.save()
        DiscountRule.objects.get_or_create(branch=br,name="۱۰ درصد سفارش بالای پنج میلیون",defaults={"trigger":"AUTO","scope":"ORDER","kind":"PERCENT","value":10,"min_order_amount":5000000,"max_discount":1000000,"priority":100,"is_active":True})
        DiscountRule.objects.get_or_create(branch=br,name="کد VIP",defaults={"trigger":"CODE","code":"VIP10","scope":"ORDER","kind":"PERCENT","value":10,"min_order_amount":0,"max_discount":1500000,"priority":10,"is_active":True})
        self.stdout.write(self.style.SUCCESS("Demo created. admin/admin1234 PIN=4321 | cashier/cashier1234"))
