from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import *
from apps.core.api.kitchen_actions import kitchen_ticket_done
from apps.dashboard.views import dashboard

r=DefaultRouter()
r.register("businesses",BusinessVS);r.register("branches",BranchVS);r.register("business-modules",BusinessModuleVS)
r.register("categories",CategoryVS);r.register("products",ProductVS);r.register("customers",CustomerVS)
r.register("halls",HallVS);r.register("tables",TableVS);r.register("table-sessions",TableSessionVS)
r.register("orders",OrderVS);r.register("payments",PaymentVS);r.register("refunds",RefundVS)
r.register("stations",StationVS);r.register("kitchen-tickets",KitchenTicketVS)
r.register("ingredient-categories",IngredientCategoryVS,basename="ingredient-category")
r.register("inventory-items",InventoryItemVS);r.register("stock-movements",StockMovementVS);r.register("recipe-items",RecipeItemVS)
r.register("pagers",PagerVS);r.register("takeaway-profiles",TakeawayProfileVS)
r.register("cash-registers",CashRegisterVS);r.register("cash-shifts",CashShiftVS);r.register("cash-movements",CashMovementVS)
r.register("suppliers",SupplierVS);r.register("purchase-invoices",PurchaseInvoiceVS);r.register("purchase-items",PurchaseItemVS);r.register("supplier-payments",SupplierPaymentVS)
r.register("expense-categories",ExpenseCategoryVS);r.register("expenses",ExpenseVS);r.register("fixed-overheads",FixedOverheadVS)
r.register("audit-logs",AuditLogVS,basename="audit-log");r.register("approval-requests",ApprovalRequestVS,basename="approval-request")
r.register("daily-closings",DailyClosingVS,basename="daily-closing");r.register("users",UserManagementVS,basename="user-management")
r.register("discount-rules",DiscountRuleVS,basename="discount-rule");r.register("staff-schedules",StaffScheduleVS,basename="staff-schedule")
r.register("attendance",AttendanceVS,basename="attendance");r.register("waste-records",WasteRecordVS,basename="waste-record")
r.register("inventory-counts",InventoryCountVS,basename="inventory-count")
r.register("stock-transfers",StockTransferVS,basename="stock-transfer")
r.register("production-formulas",ProductionFormulaVS,basename="production-formula")
r.register("production-formula-items",ProductionFormulaItemVS,basename="production-formula-item")
r.register("production-batches",ProductionBatchVS,basename="production-batch")
r.register("fiscal-settings",FiscalSettingsVS,basename="fiscal-settings")
r.register("printers",PrinterDeviceVS,basename="printer-device")
r.register("print-templates",PrintTemplateVS,basename="print-template")
r.register("print-jobs",PrintJobVS,basename="print-job")
r.register("inventory-lots",InventoryLotVS,basename="inventory-lot")
r.register("reservations",ReservationVS,basename="reservation")
r.register("loyalty-programs",LoyaltyProgramVS,basename="loyalty-program")
r.register("loyalty-accounts",CustomerLoyaltyAccountVS,basename="loyalty-account")
r.register("wallet-accounts",WalletAccountVS,basename="wallet-account")
r.register("notifications",NotificationVS,basename="notification")
r.register("sms-provider",SmsProviderConfigVS,basename="sms-provider")
r.register("online-menu-settings",OnlineMenuSettingsVS,basename="online-menu-setting")
r.register("table-qr-tokens",TableQrTokenVS,basename="table-qr-token")
r.register("online-orders",OnlineOrderVS,basename="online-order")
r.register("bill-splits",BillSplitVS,basename="bill-split")
r.register("delivery-zones",DeliveryZoneVS,basename="delivery-zone")
r.register("delivery-addresses",DeliveryAddressVS,basename="delivery-address")
r.register("couriers",CourierProfileVS,basename="courier")
r.register("delivery-assignments",DeliveryAssignmentVS,basename="delivery-assignment")
r.register("gift-cards",GiftCardVS,basename="gift-card")
r.register("payment-gateway",PaymentGatewayConfigVS,basename="payment-gateway-config")
r.register("gateway-intents",GatewayIntentVS,basename="gateway-intent")
r.register("loyalty-tiers",LoyaltyTierVS,basename="loyalty-tier")
r.register("loyalty-campaigns",LoyaltyCampaignVS,basename="loyalty-campaign")
r.register("lot-inventory-counts",LotInventoryCountVS,basename="lot-inventory-count")
r.register("push-provider",PushProviderConfigVS,basename="push-provider")


urlpatterns=[
    path("health/",health),path("me/",me),path("dashboard/",dashboard),path("checkout/",checkout),
    path("purchases/create/",create_multi_purchase),path("reports/financial/",financial_report),
    path("approvals/request/",request_approval),path("daily-close/",daily_close),
    path("reports/sales/",sales_reports),path("reports/food-cost/",food_cost),path("reports/kpi/",kpi_report),
    path("settings/context/",settings_context),path("settings/readiness/",settings_readiness),
    path("settings/onboarding/presets/",settings_onboarding_presets),path("settings/onboarding/apply/",settings_onboarding_apply),
    path("settings/health/",settings_health),path("settings/health/printer/",settings_printer_health),
    path("settings/deployment-profiles/",settings_deployment_profiles),path("settings/go-live/",settings_go_live),
    path("settings/users/create/",settings_user_create),path("settings/users/<int:user_id>/password/",settings_user_password),path("permissions/me/",permissions_me),path("permissions/matrix/",permission_matrix),
    path("manager-pin/set/",manager_pin_set),path("manager-override/",manager_override),
    path("attendance/clock-in/",attendance_clock_in),path("attendance/clock-out/",attendance_clock_out),
    path("waste/create/",waste_create),path("dashboard/branches/",branches_dashboard),
    path("inventory-counts/create/",inventory_count_create),path("stock-transfers/create/",stock_transfer_create),
    path("orders/<int:pk>/settle/",order_settle),path("checkout/preview/",checkout_preview),
    path("orders/<int:pk>/receipt-job/",receipt_job_create),path("orders/<int:pk>/receipt-payload/",receipt_payload),
    path("kitchen-tickets/<int:pk>/done/",kitchen_ticket_done),
    path("kitchen-tickets/<int:pk>/print-payload/",kitchen_print_payload),path("kitchen-tickets/<int:pk>/print-job/",kitchen_job_create),
    path("orders/<int:pk>/bill-splits/",bill_split_create),path("customers/<int:customer_id>/loyalty/redeem/",loyalty_redeem),path("customers/<int:customer_id>/wallet/credit/",wallet_credit),
    path("notifications/process/",process_notifications_api),path("online/settings/ensure/",online_settings_ensure),path("tables/<int:pk>/qr/ensure/",table_qr_ensure),path("tables/<int:pk>/qr.svg",table_qr_svg),
    path("public/qr/<uuid:token>.svg",public_table_qr_svg),path("public/menu/<slug:slug>/",public_menu_api),path("public/menu/<slug:slug>/preview/",public_order_preview),path("public/menu/<slug:slug>/orders/",public_order_create),path("public/orders/<uuid:token>/",public_order_status),

    path("gift-cards/issue/",gift_card_issue),path("gift-cards/balance/",gift_card_balance),
    path("lot-inventory-counts/create/",lot_count_create),
    path("orders/<int:pk>/transfer-items/",order_items_transfer),path("table-sessions/<int:pk>/transfer/",table_session_transfer),
    path("public/menu/<slug:slug>/push-key/",public_push_key),path("public/orders/<uuid:token>/push-subscribe/",public_push_subscribe),
    path("public/payments/<uuid:token>/callback/",public_payment_callback),path("push/generate-keys/",push_generate_keys),
    path("",include(r.urls)),
]
