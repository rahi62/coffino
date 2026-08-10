"""Runtime labels for Django Admin; database model state remains unchanged."""
from django.contrib import admin
from django.utils.functional import lazy
from django.utils.translation import get_language


APP_LABELS = {
    'accounting': 'مالی', 'accounts': 'کاربران و دسترسی‌ها', 'audit': 'ثبت رویدادها',
    'businesses': 'کسب‌وکارها', 'cashier': 'صندوق', 'catalog': 'کاتالوگ',
    'customers': 'مشتریان', 'delivery': 'ارسال', 'dining': 'سالن و میزها',
    'discounts': 'تخفیف‌ها', 'giftcards': 'کارت‌های هدیه', 'inventory': 'انبار',
    'kitchen': 'آشپزخانه', 'loyalty': 'باشگاه مشتریان', 'notifications': 'اعلان‌ها',
    'online_ordering': 'سفارش‌گیری آنلاین', 'orders': 'سفارش‌ها', 'payment_gateway': 'درگاه پرداخت',
    'payments': 'پرداخت‌ها', 'printing': 'چاپ', 'production': 'تولید',
    'purchasing': 'خرید', 'reservations': 'رزروها', 'suppliers': 'تأمین‌کنندگان',
    'takeaway': 'بیرون‌بر', 'workforce': 'نیروی انسانی',
}

MODEL_LABELS = {
    'businesses.Business': ('کسب‌وکار', 'کسب‌وکارها'),
    'businesses.Branch': ('شعبه', 'شعبه‌ها'),
    'businesses.BusinessModule': ('ماژول کسب‌وکار', 'ماژول‌های کسب‌وکار'),
    'accounts.User': ('کاربر', 'کاربران'),
    'accounts.ManagerOverrideCredential': ('مجوز تأیید مدیر', 'مجوزهای تأیید مدیر'),
    'catalog.Category': ('دسته‌بندی', 'دسته‌بندی‌ها'),
    'catalog.Product': ('محصول', 'محصولات'),
    'customers.Customer': ('مشتری', 'مشتریان'),
    'dining.Hall': ('سالن', 'سالن‌ها'), 'dining.Table': ('میز', 'میزها'),
    'dining.TableSession': ('نشست میز', 'نشست‌های میز'),
    'dining.TableTransferLog': ('ثبت انتقال میز', 'ثبت‌های انتقال میز'),
    'orders.Order': ('سفارش', 'سفارش‌ها'), 'orders.OrderItem': ('آیتم سفارش', 'آیتم‌های سفارش'),
    'payments.Payment': ('پرداخت', 'پرداخت‌ها'), 'payments.Refund': ('بازگشت وجه', 'بازگشت‌های وجه'),
    'payments.BillSplit': ('تقسیم صورت‌حساب', 'تقسیم‌های صورت‌حساب'),
    'payments.BillSplitLine': ('آیتم تقسیم صورت‌حساب', 'آیتم‌های تقسیم صورت‌حساب'),
    'kitchen.PreparationStation': ('ایستگاه آماده‌سازی', 'ایستگاه‌های آماده‌سازی'),
    'kitchen.KitchenTicket': ('فیش آشپزخانه', 'فیش‌های آشپزخانه'),
    'inventory.InventoryItem': ('کالای انبار', 'کالاهای انبار'),
    'inventory.StockMovement': ('گردش انبار', 'گردش‌های انبار'),
    'inventory.RecipeItem': ('آیتم دستور تهیه', 'آیتم‌های دستور تهیه'),
    'inventory.WasteRecord': ('ثبت ضایعات', 'ثبت‌های ضایعات'),
    'inventory.InventoryCount': ('شمارش انبار', 'شمارش‌های انبار'),
    'inventory.InventoryCountLine': ('آیتم شمارش انبار', 'آیتم‌های شمارش انبار'),
    'inventory.StockTransfer': ('انتقال موجودی', 'انتقال‌های موجودی'),
    'inventory.StockTransferLine': ('آیتم انتقال موجودی', 'آیتم‌های انتقال موجودی'),
    'inventory.InventoryLot': ('بچ انبار', 'بچ‌های انبار'),
    'inventory.LotInventoryCount': ('شمارش بچ', 'شمارش‌های بچ'),
    'inventory.LotInventoryCountLine': ('آیتم شمارش بچ', 'آیتم‌های شمارش بچ'),
    'cashier.CashRegister': ('صندوق', 'صندوق‌ها'), 'cashier.CashShift': ('شیفت صندوق', 'شیفت‌های صندوق'),
    'cashier.CashMovement': ('گردش صندوق', 'گردش‌های صندوق'),
    'takeaway.PagerDevice': ('پیجر', 'پیجرها'), 'takeaway.TakeawayProfile': ('پروفایل بیرون‌بر', 'پروفایل‌های بیرون‌بر'),
    'suppliers.Supplier': ('تأمین‌کننده', 'تأمین‌کنندگان'),
    'purchasing.PurchaseInvoice': ('فاکتور خرید', 'فاکتورهای خرید'),
    'purchasing.PurchaseItem': ('آیتم خرید', 'آیتم‌های خرید'),
    'purchasing.SupplierPayment': ('پرداخت تأمین‌کننده', 'پرداخت‌های تأمین‌کننده'),
    'accounting.ExpenseCategory': ('دسته هزینه', 'دسته‌های هزینه'),
    'accounting.Expense': ('هزینه', 'هزینه‌ها'), 'accounting.FixedOverhead': ('هزینه ثابت', 'هزینه‌های ثابت'),
    'accounting.FiscalSettings': ('تنظیمات مالیاتی', 'تنظیمات مالیاتی'),
    'audit.AuditLog': ('گزارش رویداد', 'گزارش‌های رویداد'),
    'discounts.DiscountRule': ('قانون تخفیف', 'قوانین تخفیف'),
    'workforce.StaffSchedule': ('برنامه کاری کارکنان', 'برنامه‌های کاری کارکنان'),
    'workforce.Attendance': ('حضور و غیاب', 'حضور و غیاب'),
    'production.ProductionFormula': ('فرمول تولید', 'فرمول‌های تولید'),
    'production.ProductionFormulaItem': ('آیتم فرمول تولید', 'آیتم‌های فرمول تولید'),
    'production.ProductionBatch': ('بچ تولید', 'بچ‌های تولید'),
    'production.ProductionBatchIngredient': ('ماده اولیه بچ', 'مواد اولیه بچ'),
    'printing.PrinterDevice': ('دستگاه چاپ', 'دستگاه‌های چاپ'),
    'printing.PrintTemplate': ('قالب چاپ', 'قالب‌های چاپ'), 'printing.PrintJob': ('وظیفه چاپ', 'وظایف چاپ'),
    'reservations.Reservation': ('رزرو', 'رزروها'),
    'loyalty.LoyaltyProgram': ('برنامه وفاداری', 'برنامه‌های وفاداری'),
    'loyalty.CustomerLoyaltyAccount': ('حساب وفاداری مشتری', 'حساب‌های وفاداری مشتری'),
    'loyalty.LoyaltyLedger': ('دفتر وفاداری', 'دفترهای وفاداری'),
    'loyalty.WalletAccount': ('کیف پول', 'کیف‌های پول'),
    'loyalty.WalletTransaction': ('تراکنش کیف پول', 'تراکنش‌های کیف پول'),
    'loyalty.LoyaltyTier': ('سطح وفاداری', 'سطوح وفاداری'),
    'loyalty.LoyaltyCampaign': ('کمپین وفاداری', 'کمپین‌های وفاداری'),
    'notifications.SmsProviderConfig': ('تنظیمات پیامک', 'تنظیمات پیامک'),
    'notifications.PagerProviderConfig': ('تنظیمات پیجر', 'تنظیمات پیجر'),
    'notifications.Notification': ('اعلان', 'اعلان‌ها'),
    'notifications.PushProviderConfig': ('تنظیمات اعلان پوش', 'تنظیمات اعلان پوش'),
    'notifications.PushSubscription': ('اشتراک اعلان پوش', 'اشتراک‌های اعلان پوش'),
    'online_ordering.OnlineMenuSettings': ('تنظیمات منوی آنلاین', 'تنظیمات منوی آنلاین'),
    'online_ordering.TableQrToken': ('توکن QR میز', 'توکن‌های QR میز'),
    'online_ordering.OnlineOrder': ('سفارش آنلاین', 'سفارش‌های آنلاین'),
    'delivery.DeliveryZone': ('محدوده ارسال', 'محدوده‌های ارسال'),
    'delivery.DeliveryAddress': ('آدرس ارسال', 'آدرس‌های ارسال'),
    'delivery.CourierProfile': ('پروفایل پیک', 'پروفایل‌های پیک'),
    'delivery.DeliveryAssignment': ('ماموریت ارسال', 'ماموریت‌های ارسال'),
    'giftcards.GiftCard': ('کارت هدیه', 'کارت‌های هدیه'),
    'giftcards.GiftCardTransaction': ('تراکنش کارت هدیه', 'تراکنش‌های کارت هدیه'),
    'payment_gateway.PaymentGatewayConfig': ('تنظیمات درگاه پرداخت', 'تنظیمات درگاه پرداخت'),
    'payment_gateway.GatewayIntent': ('درخواست درگاه پرداخت', 'درخواست‌های درگاه پرداخت'),
}

FIELD_LABELS = {
    'id':'شناسه', 'uuid':'شناسه یکتا', 'name':'نام', 'title':'عنوان', 'description':'توضیحات', 'notes':'یادداشت‌ها',
    'note':'یادداشت', 'code':'کد', 'number':'شماره', 'status':'وضعیت', 'enabled':'فعال', 'is_active':'فعال است',
    'is_enabled':'فعال است', 'is_available':'در دسترس است', 'is_blocked':'مسدود است', 'is_default':'پیش‌فرض است',
    'created_at':'زمان ایجاد', 'updated_at':'زمان به‌روزرسانی', 'created_by':'ایجادکننده', 'updated_by':'به‌روزرساننده',
    'business':'کسب‌وکار', 'branch':'شعبه', 'category':'دسته‌بندی', 'product':'محصول', 'customer':'مشتری',
    'supplier':'تأمین‌کننده', 'user':'کاربر', 'actor':'انجام‌دهنده', 'cashier':'صندوق‌دار', 'courier':'پیک',
    'order':'سفارش', 'order_number':'شماره سفارش', 'order_type':'نوع سفارش', 'order_types':'انواع سفارش',
    'order_item':'آیتم سفارش', 'order_items':'آیتم‌های سفارش', 'payment':'پرداخت', 'payment_method':'روش پرداخت',
    'payment_status':'وضعیت پرداخت', 'payment_mode':'حالت پرداخت', 'bill_split':'تقسیم صورت‌حساب',
    'amount':'مبلغ', 'paid_amount':'مبلغ پرداخت‌شده', 'tendered_amount':'وجه دریافتی', 'change_amount':'باقی‌مانده پرداختی',
    'subtotal':'جمع جزء', 'grand_total':'جمع کل', 'total_amount':'مبلغ کل', 'total_cost':'هزینه کل',
    'line_total':'جمع آیتم', 'unit_price':'قیمت واحد', 'unit_cost':'هزینه واحد', 'average_cost':'میانگین هزینه',
    'discount_total':'مبلغ تخفیف', 'discount_rule':'قانون تخفیف', 'discount_reason':'دلیل تخفیف',
    'tax_total':'مالیات', 'tax_rate':'نرخ مالیات', 'tax_enabled':'مالیات فعال است',
    'service_charge_total':'هزینه خدمات', 'service_charge_rate':'نرخ خدمات', 'service_charge_enabled':'هزینه خدمات فعال است',
    'delivery_fee':'هزینه ارسال', 'delivery_fee_total':'جمع هزینه ارسال', 'delivery_fee_taxable':'هزینه ارسال مشمول مالیات است',
    'quantity':'تعداد', 'current_stock':'موجودی فعلی', 'minimum_stock':'حداقل موجودی', 'difference':'اختلاف',
    'inventory_item':'کالای انبار', 'stock_item':'کالای انبار', 'item':'آیتم', 'item_code':'کد آیتم',
    'source_item':'آیتم مبدأ', 'destination_item':'آیتم مقصد', 'source_branch':'شعبه مبدأ', 'destination_branch':'شعبه مقصد',
    'source':'منبع', 'source_type':'نوع منبع', 'source_id':'شناسه منبع', 'transfer':'انتقال',
    'table':'میز', 'table_session':'نشست میز', 'hall':'سالن', 'from_table':'میز مبدأ', 'to_table':'میز مقصد',
    'capacity':'ظرفیت', 'is_open':'باز است', 'opened_at':'زمان باز شدن', 'closed_at':'زمان بسته شدن',
    'customer_name':'نام مشتری', 'customer_phone':'تلفن مشتری', 'phone':'تلفن', 'email':'ایمیل', 'address':'نشانی',
    'recipient':'گیرنده', 'recipient_name':'نام گیرنده', 'postal_code':'کد پستی', 'latitude':'عرض جغرافیایی', 'longitude':'طول جغرافیایی',
    'username':'نام کاربری', 'password':'رمز عبور', 'first_name':'نام', 'last_name':'نام خانوادگی',
    'last_login':'آخرین ورود', 'date_joined':'تاریخ عضویت', 'is_staff':'دسترسی مدیریت دارد',
    'is_superuser':'مدیر کل است', 'groups':'گروه‌ها', 'user_permissions':'مجوزهای کاربر', 'role':'نقش',
    'permission_overrides':'مجوزهای اختصاصی', 'action':'عملیات', 'before':'پیش از تغییر', 'after':'پس از تغییر',
    'entity_type':'نوع موجودیت', 'entity_id':'شناسه موجودیت', 'ip_address':'نشانی IP', 'user_agent':'مرورگر کاربر',
    'event':'رویداد', 'channel':'کانال', 'body':'متن', 'subject':'موضوع', 'sent_at':'زمان ارسال',
    'next_attempt_at':'تلاش بعدی', 'attempts':'تعداد تلاش', 'last_error':'آخرین خطا', 'dedupe_key':'کلید جلوگیری از تکرار',
    'endpoint':'نشانی سرویس', 'endpoint_url':'نشانی سرویس', 'headers':'سرآیندها', 'timeout_seconds':'مهلت پاسخ (ثانیه)',
    'api_key_encrypted':'کلید API رمزنگاری‌شده', 'merchant_id_encrypted':'شناسه پذیرنده رمزنگاری‌شده',
    'vapid_public_key':'کلید عمومی VAPID', 'vapid_private_key_encrypted':'کلید خصوصی VAPID رمزنگاری‌شده',
    'callback_url':'نشانی بازگشت', 'callback_base_url':'نشانی پایه بازگشت', 'gateway_url':'نشانی درگاه',
    'verify_url':'نشانی تأیید', 'refund_url':'نشانی بازگشت وجه', 'request_url':'نشانی درخواست',
    'request_payload':'داده درخواست', 'verify_payload':'داده تأیید', 'payload':'داده', 'metadata':'داده‌های تکمیلی',
    'reference':'مرجع', 'reference_number':'شماره مرجع', 'reference_type':'نوع مرجع',
    'invoice':'فاکتور', 'invoice_number':'شماره فاکتور', 'invoice_date':'تاریخ فاکتور', 'purchase_invoice':'فاکتور خرید',
    'purchaser_name':'نام خریدار', 'received_by':'دریافت‌کننده', 'received_at':'زمان دریافت',
    'register':'صندوق', 'shift':'شیفت', 'initial_balance':'مانده آغازین', 'opening_balance':'مانده افتتاح',
    'closing_balance':'مانده پایان', 'expected_cash':'نقد مورد انتظار', 'opened_by':'بازکننده',
    'price':'قیمت', 'sku':'شناسه کالا', 'product_name':'نام محصول', 'product_type':'نوع محصول',
    'preparation_station':'ایستگاه آماده‌سازی', 'station':'ایستگاه', 'estimated_minutes':'زمان تقریبی (دقیقه)',
    'priority':'اولویت', 'printed_at':'زمان چاپ', 'printer':'چاپگر', 'paper_width':'عرض کاغذ',
    'header':'سربرگ', 'footer':'پاورقی', 'show_tax':'نمایش مالیات', 'show_service_charge':'نمایش هزینه خدمات',
    'show_customer':'نمایش مشتری', 'receipt_service_label':'عنوان هزینه خدمات رسید', 'receipt_tax_label':'عنوان مالیات رسید',
    'reserved_for':'زمان رزرو', 'party_size':'تعداد نفرات', 'duration_minutes':'مدت (دقیقه)', 'seated_session':'نشست ثبت‌شده',
    'zone':'محدوده', 'delivery_address':'آدرس ارسال', 'min_order_amount':'حداقل مبلغ سفارش',
    'free_delivery_above':'ارسال رایگان از مبلغ', 'assigned_at':'زمان تخصیص', 'picked_up_at':'زمان تحویل به پیک',
    'delivered_at':'زمان تحویل', 'proof_note':'یادداشت تحویل', 'vehicle':'وسیله نقلیه',
    'gift_card':'کارت هدیه', 'card':'کارت', 'code_hash':'هش کد', 'code_last4':'چهار رقم آخر کد',
    'expires_at':'زمان انقضا', 'balance':'مانده', 'balance_after':'مانده پس از تراکنش',
    'points':'امتیاز', 'points_balance':'مانده امتیاز', 'bonus_points':'امتیاز تشویقی',
    'welcome_points':'امتیاز خوش‌آمدگویی', 'lifetime_points':'امتیاز کل', 'tier':'سطح',
    'point_wallet_value':'ارزش هر امتیاز', 'amount_per_point':'مبلغ هر امتیاز', 'multiplier':'ضریب',
    'starts_at':'زمان شروع', 'ends_at':'زمان پایان', 'weekdays':'روزهای هفته', 'frequency':'تناوب',
    'formula':'فرمول', 'batch':'بچ', 'batch_number':'شماره بچ', 'output_item':'محصول خروجی',
    'output_quantity':'تعداد خروجی', 'produced_quantity':'تعداد تولیدشده', 'shelf_life_days':'ماندگاری (روز)',
    'lot':'بچ انبار', 'lot_number':'شماره بچ', 'lot_tracked':'بچ‌محور است', 'expires_at':'تاریخ انقضا',
    'counted_quantity':'تعداد شمارش‌شده', 'counted_by':'شمارش‌کننده', 'system_quantity':'تعداد سیستمی',
    'posted_at':'زمان ثبت نهایی', 'posted_by':'ثبت‌کننده نهایی', 'reason':'دلیل', 'method':'روش',
    'accepting_orders':'پذیرش سفارش', 'allow_delivery':'اجازه ارسال', 'allow_pickup':'اجازه بیرون‌بر',
    'allow_takeaway':'اجازه بیرون‌بر', 'allow_dine_in_qr':'اجازه سفارش QR حضوری', 'public_slug':'شناسه عمومی',
    'public_base_url':'نشانی پایه عمومی', 'table_token':'توکن میز', 'token':'توکن', 'access_token':'توکن دسترسی',
    'idempotency_key':'کلید تکرارناپذیری', 'idempotency_fingerprint':'اثر انگشت درخواست',
    'is_walk_in':'مشتری حضوری است', 'pager':'پیجر', 'pickup_number':'شماره تحویل', 'notified_at':'زمان اطلاع‌رسانی',
    'sender':'فرستنده', 'sender_field':'فیلد فرستنده', 'phone_field':'فیلد تلفن', 'message_field':'فیلد پیام',
    'auth':'اطلاعات احراز هویت', 'p256dh':'کلید P256DH', 'authority':'مرجع', 'scope':'دامنه دسترسی',
    'deployment_type':'نوع استقرار', 'business_type':'نوع کسب‌وکار', 'system_name':'نام سامانه',
    'config':'پیکربندی', 'key':'کلید', 'value':'مقدار', 'extra':'اطلاعات اضافی', 'error':'خطا',
    'account':'حساب', 'clock_in':'زمان ورود', 'clock_out':'زمان خروج', 'count':'تعداد',
    'customer_count':'تعداد مشتریان', 'document_type':'نوع سند', 'entry_type':'نوع ثبت', 'kind':'نوع',
    'last_purchase_cost':'آخرین هزینه خرید', 'movement_type':'نوع گردش', 'occurred_at':'زمان وقوع',
    'payer_label':'عنوان پرداخت‌کننده', 'payment_url':'نشانی پرداخت', 'pin_hash':'هش پین',
    'plate':'پلاک', 'points_multiplier':'ضریب امتیاز', 'provider':'ارائه‌دهنده',
    'provider_name':'نام ارائه‌دهنده', 'quantity_received':'مقدار دریافت‌شده',
    'quantity_remaining':'مقدار باقی‌مانده', 'reference_id':'شناسه مرجع', 'requested_by':'درخواست‌کننده',
    'sandbox':'حالت آزمایشی', 'session':'نشست', 'sort_order':'ترتیب نمایش',
    'transaction_type':'نوع تراکنش', 'transferred_by':'انتقال‌دهنده', 'trigger':'محرک', 'unit':'واحد',
    'unit_cost_snapshot':'تصویر هزینه واحد', 'variance':'مغایرت', 'variance_value':'مقدار مغایرت',
    'wallet':'کیف پول', 'welcome_text':'متن خوش‌آمدگویی', 'work_date':'تاریخ کاری',
    'enabled':'فعال', 'is_default':'پیش‌فرض است', 'max_discount':'حداکثر تخفیف', 'requires_manager':'نیازمند تأیید مدیر',
    'min_lifetime_points':'حداقل امتیاز کل', 'min_redeem_points':'حداقل امتیاز مصرفی',
    'prices_include_tax':'قیمت شامل مالیات است', 'service_charge_is_revenue':'هزینه خدمات درآمد است',
    'service_charge_order_types':'انواع سفارش مشمول خدمات', 'verified_at':'زمان تأیید', 'paid_at':'زمان پرداخت',
}

SECTION_LABELS = {
    'Personal info':'اطلاعات شخصی', 'Permissions':'دسترسی‌ها', 'Important dates':'تاریخ‌های مهم',
    'Cafino tenant':'محدوده کافینو',
}


def is_persian():
    return (get_language() or 'fa').lower().startswith('fa')


def localized_text(persian, english):
    if persian is None and english is None:
        return None
    return lazy(lambda: persian if is_persian() else english, str)()


def field_label(name, fallback=None):
    return FIELD_LABELS.get(name, fallback or name) if is_persian() else (fallback or name)


class PersianAdminMixin:
    def get_form(self, request, obj=None, change=False, **kwargs):
        # Django's UserAdmin keeps ``change`` keyword-only through **kwargs.
        # Passing it positionally breaks the user change page with a 500.
        form = super().get_form(request, obj, change=change, **kwargs)
        if is_persian():
            for name, field in form.base_fields.items():
                field.label = field_label(name, field.label)
        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        return tuple(
            (localized_text(SECTION_LABELS.get(title, title), title) if title is not None else None, options)
            for title, options in fieldsets
        )


def localize_admin():
    """Apply the labels after Django has auto-discovered all app admins."""
    for app_label, title in APP_LABELS.items():
        try:
            model = next(model for model in admin.site._registry if model._meta.app_label == app_label)
        except StopIteration:
            continue
        model._meta.app_config.verbose_name = localized_text(title, model._meta.app_config.verbose_name)
    for model, labels in MODEL_LABELS.items():
        for registered_model in admin.site._registry:
            if registered_model._meta.label == model:
                registered_model._meta.verbose_name = localized_text(labels[0], registered_model._meta.verbose_name)
                registered_model._meta.verbose_name_plural = localized_text(labels[1], registered_model._meta.verbose_name_plural)
                break
    for model, model_admin in list(admin.site._registry.items()):
        if model._meta.app_label in {'auth', 'contenttypes', 'sessions'} or getattr(model_admin, '_cafino_persian_labels', False):
            continue
        localized_class = type(
            f'Persian{model_admin.__class__.__name__}',
            (PersianAdminMixin, model_admin.__class__),
            {'_cafino_persian_labels': True},
        )
        admin.site.unregister(model)
        admin.site.register(model, localized_class)
    if not getattr(admin.site, '_cafino_businesses_first', False):
        original_get_app_list = admin.site.get_app_list

        def get_app_list(request, app_label=None):
            app_list = original_get_app_list(request, app_label)
            app_list.sort(key=lambda app: (app['app_label'] != 'businesses', app['name']))
            for app in app_list:
                if app['app_label'] == 'businesses':
                    app['models'].sort(
                        key=lambda model: {
                            'Business': 0, 'Branch': 1, 'BusinessModule': 2,
                        }.get(model['object_name'], 99)
                    )
            return app_list

        admin.site.get_app_list = get_app_list
        admin.site._cafino_businesses_first = True
