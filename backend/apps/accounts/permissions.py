from rest_framework.permissions import BasePermission

PERMISSION_GROUPS={
 'فروش و سفارش':[
  ('orders.view','مشاهده سفارش‌ها'),('orders.create','ثبت سفارش'),('orders.complete','تکمیل سفارش'),('orders.void','Void مستقیم'),('payments.create','ثبت پرداخت'),
  ('discount.manual','تخفیف دستی'),('discount.rules.manage','مدیریت قوانین تخفیف'),('payments.refund','Refund'),('payments.split','Split Bill آیتم‌محور'),('orders.transfer','انتقال آیتم بین سفارش‌ها'),
 ],
 'صندوق و مالی':[
  ('cashier.use','کار با صندوق'),('cashier.view','مشاهده صندوق'),('daily_close.execute','بستن روز مالی'),
  ('reports.view','مشاهده گزارش‌ها'),('food_cost.view','مشاهده Food Cost'),('expenses.manage','مدیریت هزینه‌ها'),
 ],
 'عملیات':[
  ('tables.use','مدیریت میز'),('reservations.manage','مدیریت رزرو'),('kitchen.view','مشاهده آشپزخانه'),('kitchen.update','تغییر وضعیت آشپزخانه'),
  ('inventory.view','مشاهده انبار'),('inventory.manage','مدیریت انبار'),('waste.manage','ثبت ضایعات'),
  ('purchasing.view','مشاهده خرید'),('purchasing.manage','ثبت و مدیریت خرید'),('loyalty.manage','باشگاه مشتریان و کیف پول'),('giftcards.manage','مدیریت کارت هدیه'),('notifications.manage','Notification/SMS/Push'),('online_ordering.manage','مدیریت سفارش آنلاین'),('delivery.manage','مدیریت ارسال و پیک'),('suppliers.view','مشاهده تأمین‌کننده'),
  ('inventory.count','شمارش فیزیکی انبار'),('inventory.lot_count','شمارش Lot'),('inventory.transfer','انتقال بین شعب'),
  ('production.manage','مدیریت تولید Batch'),('printing.use','چاپ رسید/تیکت'),
 ],
 'مدیریت':[
  ('audit.view','مشاهده Audit'),('approvals.decide','تأیید درخواست‌ها'),('permissions.manage','مدیریت دسترسی'),
  ('manager_pin.manage','مدیریت PIN مدیر'),('workforce.manage','مدیریت کارکنان'),('workforce.clock','ثبت حضور'),
  ('settings.manage','مدیریت تنظیمات کسب‌وکار'),('business.manage','مدیریت کسب‌وکار'),('branches.manage','مدیریت شعب'),('branches.dashboard','داشبورد چندشعبه‌ای'),('fiscal.manage','تنظیم مالیات و حق سرویس'),('payment_gateway.manage','تنظیم درگاه پرداخت'),('printing.manage','مدیریت پرینتر'),
 ],
}
PERMISSION_MODULES={
 'orders.view':'POS','orders.create':'POS','orders.complete':'POS','orders.void':'POS','orders.transfer':'POS',
 'payments.create':'POS','payments.refund':'POS','payments.split':'POS','discount.manual':'POS','discount.rules.manage':'POS',
 'cashier.use':'POS','cashier.view':'POS','daily_close.execute':'ACCOUNTING','reports.view':'REPORTING','food_cost.view':'REPORTING','expenses.manage':'ACCOUNTING',
 'tables.use':'DINE_IN','reservations.manage':'RESERVATION','kitchen.view':'KITCHEN_DISPLAY','kitchen.update':'KITCHEN_DISPLAY',
 'inventory.view':'INVENTORY','inventory.manage':'INVENTORY','inventory.count':'INVENTORY','inventory.lot_count':'INVENTORY','inventory.transfer':'INVENTORY','waste.manage':'INVENTORY',
 'purchasing.view':'PURCHASING','purchasing.manage':'PURCHASING','suppliers.view':'PURCHASING','production.manage':'PRODUCTION',
 'loyalty.manage':'LOYALTY','giftcards.manage':'GIFT_CARD','notifications.manage':'NOTIFICATIONS','online_ordering.manage':'ONLINE_ORDERING','delivery.manage':'DELIVERY',
 'branches.dashboard':'MULTI_BRANCH','fiscal.manage':'ACCOUNTING','payment_gateway.manage':'PAYMENT_GATEWAY','printing.manage':'PRINTING','printing.use':'PRINTING',
}
def _module_enabled(user,code):
    key=PERMISSION_MODULES.get(code)
    if not key or not user or not user.is_authenticated or user.is_superuser:
        return True
    business_id=getattr(user,'business_id',None)
    if not business_id and getattr(user,'branch_id',None):
        business_id=user.branch.business_id
    if not business_id:
        return False
    cache=getattr(user,'_cafino_module_cache',None)
    if cache is None:
        from apps.businesses.models import BusinessModule
        cache={k:enabled for k,enabled in BusinessModule.objects.filter(business_id=business_id).values_list('key','enabled')}
        user._cafino_module_cache=cache
    return cache.get(key,True)
ALL_PERMISSION_CODES=[code for rows in PERMISSION_GROUPS.values() for code,_ in rows]
MANAGER_RESTRICTED_PERMISSIONS={'business.manage','branches.manage','branches.dashboard','permissions.manage'}
ROLE_PERMISSIONS={
 'OWNER':{'*'},'MANAGER':{'*'},
 'CASHIER':{'orders.view','orders.create','orders.complete','payments.create','payments.split','orders.transfer','tables.use','cashier.use','printing.use','discount.request','void.request','workforce.clock'},
 'WAITER':{'orders.view','orders.create','orders.complete','orders.transfer','tables.use','reservations.manage','workforce.clock'},
 'KITCHEN':{'kitchen.view','kitchen.update','workforce.clock'},
 'INVENTORY':{'inventory.view','inventory.manage','inventory.count','inventory.lot_count','inventory.transfer','production.manage','waste.manage','purchasing.view','purchasing.manage','food_cost.view','workforce.clock'},
 'ACCOUNTANT':{'reports.view','food_cost.view','expenses.manage','purchasing.view','purchasing.manage','suppliers.view','cashier.view','audit.view','workforce.clock'},
}
def has_perm(user,code):
    if not user or not user.is_authenticated:return False
    if user.is_superuser:return True
    if not _module_enabled(user,code):return False
    overrides=user.permission_overrides or {}
    if user.role=='MANAGER' and user.branch_id and code in MANAGER_RESTRICTED_PERMISSIONS:
        return False
    if code in overrides:return bool(overrides[code])
    allowed=ROLE_PERMISSIONS.get(user.role,set())
    return '*' in allowed or code in allowed
class HasCafinoPermission(BasePermission):
    permission_code=None
    def has_permission(self,request,view):
        code=getattr(view,'cafino_permission',None) or self.permission_code
        return True if not code else has_perm(request.user,code)
