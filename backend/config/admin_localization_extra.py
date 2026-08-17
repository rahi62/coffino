"""Additional admin labels for models/fields introduced after the baseline localization map."""

from .admin_localization import FIELD_LABELS, MODEL_LABELS


MODEL_LABELS.update({
    'accounting.BankAccount': ('حساب بانکی', 'حساب‌های بانکی'),
    'inventory.IngredientCategory': ('دسته ماده اولیه', 'دسته‌های مواد اولیه'),
})

FIELD_LABELS.update({
    'bank_account': 'حساب بانکی',
    'bank_name': 'نام بانک',
    'holder_name': 'نام صاحب حساب',
    'identifier_last4': 'چهار نویسه پایانی شناسه',
    'layout': 'چیدمان',
    'material_category': 'دسته ماده اولیه',
    'pager_field': 'فیلد شناسه پیجر',
    'ready_notification_method': 'روش اعلان آماده‌شدن سفارش',
})
