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
  ('business.manage','مدیریت کسب‌وکار'),('branches.manage','مدیریت شعب'),('branches.dashboard','داشبورد چندشعبه‌ای'),('fiscal.manage','تنظیم مالیات و حق سرویس'),('payment_gateway.manage','تنظیم درگاه پرداخت'),('printing.manage','مدیریت پرینتر'),
 ],
}
ALL_PERMISSION_CODES=[code for rows in PERMISSION_GROUPS.values() for code,_ in rows]
ROLE_PERMISSIONS={
 'OWNER':{'*'},'MANAGER':{'*'},
 'CASHIER':{'orders.view','orders.create','orders.complete','payments.create','payments.split','orders.transfer','cashier.use','printing.use','discount.request','void.request','workforce.clock'},
 'WAITER':{'orders.view','orders.create','orders.complete','orders.transfer','tables.use','reservations.manage','workforce.clock'},
 'KITCHEN':{'kitchen.view','kitchen.update','workforce.clock'},
 'INVENTORY':{'inventory.view','inventory.manage','inventory.count','inventory.lot_count','inventory.transfer','production.manage','waste.manage','purchasing.view','purchasing.manage','food_cost.view','workforce.clock'},
 'ACCOUNTANT':{'reports.view','food_cost.view','expenses.manage','purchasing.view','purchasing.manage','suppliers.view','cashier.view','audit.view','workforce.clock'},
}
def has_perm(user,code):
    if not user or not user.is_authenticated:return False
    if user.is_superuser:return True
    overrides=user.permission_overrides or {}
    if code in overrides:return bool(overrides[code])
    allowed=ROLE_PERMISSIONS.get(user.role,set())
    return '*' in allowed or code in allowed
class HasCafinoPermission(BasePermission):
    permission_code=None
    def has_permission(self,request,view):
        code=getattr(view,'cafino_permission',None) or self.permission_code
        return True if not code else has_perm(request.user,code)
