export type Locale = "fa" | "en";

type MessageCatalog = Record<string, string>;

const fa: MessageCatalog = {
  "error.generic": "انجام این عملیات در حال حاضر ممکن نیست. دوباره تلاش کنید.",
  "error.network": "ارتباط با سرور برقرار نشد. اتصال اینترنت یا سرویس را بررسی کنید.",
  "error.unauthorized": "نشست شما منقضی شده است. دوباره وارد شوید.",
  "error.forbidden": "اجازه انجام این عملیات را ندارید.",
  "error.not_found": "اطلاعات درخواستی پیدا نشد.",
  "error.rate_limit": "تعداد درخواست‌ها بیش از حد مجاز است. کمی بعد دوباره تلاش کنید.",
  "error.server": "سرویس موقتاً در دسترس نیست. کمی بعد دوباره تلاش کنید.",
  "error.conflict": "این عملیات با وضعیت فعلی اطلاعات سازگار نیست. صفحه را تازه‌سازی کنید.",
  "error.validation": "اطلاعات واردشده معتبر نیست. موارد را بررسی کنید.",
  "error.order_creation_failed": "ثبت سفارش در حال حاضر ممکن نیست. دوباره تلاش کنید.",
  "error.payment_initialization_failed": "شروع پرداخت آنلاین در حال حاضر ممکن نیست.",
  "error.invalid_product": "یکی از اقلام انتخاب‌شده معتبر یا قابل سفارش نیست.",
  "error.invalid_order": "اطلاعات سفارش معتبر نیست.",
  "error.invalid_delivery_zone": "محدوده ارسال انتخاب‌شده معتبر نیست.",
  "status.DRAFT": "پیش‌نویس",
  "status.POSTED": "ثبت نهایی",
  "status.PENDING": "در انتظار",
  "status.CONFIRMED": "تأییدشده",
  "status.RECEIVED": "دریافت‌شده",
  "status.ACCEPTED": "پذیرفته‌شده",
  "status.IN_PROGRESS": "در حال آماده‌سازی",
  "status.PREPARING": "در حال آماده‌سازی",
  "status.READY": "آماده",
  "status.COMPLETED": "تکمیل‌شده",
  "status.CANCELLED": "لغوشده",
  "status.PAID": "پرداخت‌شده",
  "status.UNPAID": "پرداخت‌نشده",
  "status.PARTIALLY_PAID": "بخشی پرداخت‌شده",
  "status.PARTIALLY_REFUNDED": "بخشی برگشت‌خورده",
  "status.REFUNDED": "برگشت‌خورده",
  "status.PAYMENT_PENDING": "در انتظار پرداخت",
  "status.WAITING": "در انتظار",
  "status.ASSIGNED": "اختصاص‌یافته",
  "status.PICKED_UP": "تحویل‌گرفته‌شده",
  "status.DELIVERED": "تحویل‌شده",
  "status.FREE": "آزاد",
  "status.OCCUPIED": "اشغال",
  "status.RESERVED": "رزروشده",
  "status.WAITING_PAYMENT": "در انتظار پرداخت",
  "status.CASH": "نقدی",
  "status.POS": "کارت‌خوان",
  "status.ONLINE": "آنلاین",
  "status.CREDIT": "اعتباری",
  "status.WALLET": "کیف پول",
  "status.GIFT_CARD": "کارت هدیه",
  "status.DINE_IN": "سالن",
  "status.TAKEAWAY": "بیرون‌بر",
  "status.PICKUP": "تحویل حضوری",
  "status.DELIVERY": "ارسال",
  "status.PAY_AT_COUNTER": "پرداخت در صندوق",
  "status.NEW": "جدید",
  "status.DONE": "تحویل‌شده",
  "status.HANDED_OVER": "تحویل‌شده",
  "status.SUCCEEDED": "موفق",
  "status.FAILED": "ناموفق",
  "status.REJECTED": "ردشده",
  "status.APPROVED": "تأییدشده",
  "status.OPEN": "باز",
  "status.PARTIAL": "بخشی",
  "status.AVAILABLE": "آزاد",
  "status.BUSY": "مشغول",
  "status.OFFLINE": "غیرفعال",
  "status.DISABLED": "غیرفعال",
  "status.SEATED": "مستقرشده",
  "status.NO_SHOW": "عدم مراجعه",
  "status.PROCESSING": "در حال ارسال",
  "status.SENT": "ارسال‌شده",
  "status.IN_APP": "داخل برنامه",
  "status.SMS": "پیامک",
  "status.PAGER": "پیجر",
  "status.PUSH": "اعلان دستگاه",
  "status.SALE": "فروش نقدی",
  "status.CASH_IN": "ورود وجه نقد",
  "status.CASH_OUT": "خروج وجه نقد",
  "status.EXPENSE": "هزینه نقدی",
  "status.SUPPLIER_PAYMENT": "پرداخت تأمین‌کننده",
  "status.ADJUSTMENT": "اصلاح",
  "status.PURCHASE": "خرید",
  "status.SALE_CONSUMPTION": "مصرف فروش",
  "status.WASTE": "ضایعات",
  "status.RETURN": "برگشت",
  "status.TRANSFER_IN": "انتقال ورودی",
  "status.TRANSFER_OUT": "انتقال خروجی",
  "status.DISCOUNT": "تخفیف",
  "status.VOID": "لغو سفارش",
  "status.CREATED": "ایجادشده",
  "status.REDIRECTED": "هدایت‌شده",
  "status.VERIFIED": "تأییدشده",
  "label.payment": "پرداخت",
  "label.order": "سفارش",
  "label.refund": "برگشت وجه",
  "label.void": "لغو سفارش",
  "label.receipt": "رسید",
  "label.kitchen": "آشپزخانه",
  "label.batch": "بچ تولید",
  "label.lot": "بچ/سری ساخت",
  "label.expiry": "انقضا",
  "label.cost": "بها",
  "label.cash_ledger": "دفتر گردش نقدی",
  "label.split_bill": "تقسیم صورتحساب",
  "label.service_charge": "حق سرویس",
  "label.break_even": "نقطه سربه‌سر",
  "label.food_cost": "بهای مواد مصرفی",
  "label.loyalty": "باشگاه مشتریان",
  "label.audit_log": "گزارش رویدادها",
  "label.local_tools": "ابزارهای محلی",
  "label.gift_card": "کارت هدیه",
  "label.payment_gateway": "درگاه پرداخت",
  "label.public_link": "نشانی عمومی",
  "label.qr_code": "کد اسکن",
  "label.average_ticket": "میانگین مبلغ سفارش",
  "label.gross_margin": "حاشیه سود ناخالص",
  "label.refund_rate": "نرخ برگشت وجه",
  "label.top_product": "پرفروش‌ترین محصول",
  "label.expired_blocked": "منقضی/مسدود",
  "label.tracking": "رهگیری سری ساخت",
  "label.production": "تولید",
  "label.finished_product": "محصول نهایی",
  "label.development": "آزمایشی",
  "label.provider": "ارائه‌دهنده",
  "label.api_key": "کلید دسترسی",
  "label.callback_url": "نشانی بازگشت پرداخت",
  "label.refund_url": "نشانی بازگشت وجه",
  "label.pin": "رمز مدیر",
  "label.sms": "پیامک",
  "label.unknown_status": "ثبت‌شده",
  "nav.logout": "خروج",
};

// Add a complete catalog for a new locale here. UI code references stable keys, not Persian text.
const catalogs: Record<Locale, MessageCatalog> = { fa, en: {} };
let activeLocale: Locale = "fa";

export function setLocale(locale: Locale) {
  activeLocale = locale;
  if (typeof window !== "undefined") localStorage.setItem("cafino_locale", locale);
}

export function getLocale(): Locale {
  if (typeof window === "undefined") return activeLocale;
  const stored = localStorage.getItem("cafino_locale");
  return stored === "en" || stored === "fa" ? stored : activeLocale;
}

export function t(key: string, fallback?: string) {
  const locale = getLocale();
  return catalogs[locale][key] ?? catalogs.fa[key] ?? fallback ?? key;
}

export function label(value: unknown) {
  const key = String(value ?? "").trim();
  if (!key) return "—";
  const translated = t(`status.${key}`, key);
  // Codes are implementation details. For an unmapped future API value, keep
  // the interface readable until a translator adds its stable catalog entry.
  return getLocale() === "fa" && translated === key && /[A-Za-z]/.test(key)
    ? t("label.unknown_status")
    : translated;
}

const legacyTerms: Array<[RegExp, string]> = [
  [/Payment Intent/gi, "درخواست پرداخت"], [/Payment/gi, "پرداخت"],
  [/Refund/gi, "برگشت وجه"], [/Void/gi, "لغو سفارش"], [/Order/gi, "سفارش"],
  [/Split Bill/gi, "تقسیم صورتحساب"], [/Split/gi, "تقسیم"],
  [/Cash Ledger/gi, "دفتر گردش نقدی"], [/Ledger/gi, "دفتر گردش"],
  [/Lot Tracking/gi, "رهگیری سری ساخت"], [/Lot/gi, "سری ساخت"],
  [/Batch/gi, "بچ تولید"], [/Food Cost/gi, "بهای مواد مصرفی"],
  [/Break-even/gi, "نقطه سربه‌سر"], [/Loyalty/gi, "باشگاه مشتریان"],
  [/Service Charge/gi, "حق سرویس"], [/Merchant ID/gi, "شناسه پذیرنده"],
  [/API Key/gi, "کلید دسترسی"], [/Callback/gi, "بازگشت"],
  [/Backend/gi, "سامانه"], [/Generic/gi, "عمومی"], [/Mock/gi, "آزمایشی"],
  [/Expired/gi, "منقضی"], [/Blocked/gi, "مسدود"], [/PIN/gi, "رمز"],
  [/SMS/gi, "پیامک"], [/QR/gi, "کد اسکن"], [/POS/gi, "کارت‌خوان"],
  [/FEFO/gi, "گردش بر مبنای نزدیک‌ترین انقضا"], [/KPI/gi, "شاخص"],
  [/Local/gi, "محلی"], [/PrintJob/gi, "صف چاپ"], [/Kitchen/gi, "آشپزخانه"],
  [/DINE_IN/gi, "سالن"], [/TAKEAWAY/gi, "بیرون‌بر"], [/PICKUP/gi, "تحویل حضوری"],
  [/DELIVERY/gi, "ارسال"], [/CASH/gi, "نقدی"], [/ONLINE/gi, "آنلاین"],
];

export function localizeLegacyText(text: string) {
  return legacyTerms.reduce((result, [pattern, replacement]) => result.replace(pattern, replacement), text);
}

export function userMessage(payload: unknown, status?: number) {
  let data: unknown = payload;
  if (typeof payload === "string") {
    try { data = JSON.parse(payload); } catch { data = payload; }
  }
  if (typeof data === "object" && data !== null) {
    const body = data as { code?: string; detail?: unknown; message?: unknown; [key:string]:unknown };
    const fieldError = Object.entries(body).find(([key,value]) => !["code","detail","message"].includes(key) && (typeof value === "string" || (Array.isArray(value) && typeof value[0] === "string")));
    if (fieldError) {
      const value = fieldError[1];
      const candidate = Array.isArray(value) ? value[0] : value;
      if (typeof candidate === "string" && !/[A-Za-z]/.test(candidate)) return localizeLegacyText(candidate);
    }
    if (body.code) {
      const message = t(`error.${body.code}`);
      return message.startsWith("error.") ? t("error.generic") : message;
    }
    const message = typeof body.detail === "string" ? body.detail : typeof body.message === "string" ? body.message : undefined;
    if (message) {
      const localized = localizeLegacyText(message);
      // Framework and provider details are not a suitable customer-facing message.
      if (getLocale() === "fa" && /[A-Za-z]/.test(localized)) {
        return status === 400 ? t("error.validation") : t("error.generic");
      }
      return localized;
    }
  }
  if (status === 429) return t("error.rate_limit");
  if (status !== undefined && status >= 500) return t("error.server");
  if (status === 401) return t("error.unauthorized");
  if (status === 403) return t("error.forbidden");
  if (status === 404) return t("error.not_found");
  if (status === 409) return t("error.conflict");
  if (status === 400) return t("error.validation");
  return t("error.generic");
}
