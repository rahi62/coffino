from .shared import *
from .shared import BaseVS, _branch_accessible

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health(request): return Response({"status":"ok","service":"cafino-backend"})

@api_view(["GET"])
def me(request):
    return Response({
        "id":request.user.id,"username":request.user.username,"role":request.user.role,
        "business":request.user.business_id,"branch":request.user.branch_id,
        "email":request.user.email,"mobile":request.user.mobile,
        "mobile_verified":request.user.mobile_verified_at is not None,
        "business_id":request.user.business_id,"branch_id":request.user.branch_id,
        "is_platform_admin":bool(request.user.is_superuser)
    })

def _ready_notification_capabilities(branch):
    from apps.notifications.models import PagerProviderConfig, SmsProviderConfig
    enabled=BusinessModule.objects.filter(business=branch.business,key='NOTIFICATIONS',enabled=True).exists()
    disabled=BusinessModule.objects.filter(business=branch.business,key='NOTIFICATIONS',enabled=False).exists()
    module_allowed=enabled or not disabled
    sms=module_allowed and SmsProviderConfig.objects.filter(branch=branch,is_active=True).exclude(endpoint_url='').exists()
    pager=module_allowed and PagerProviderConfig.objects.filter(branch=branch,is_active=True).exclude(endpoint_url='').exists()
    return {'sms':sms,'pager':pager and PagerDevice.objects.filter(branch=branch,status='AVAILABLE').exists()}

@api_view(["GET"])
def checkout_notification_options(request):
    if not has_perm(request.user,'orders.create'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.query_params.get('branch'))
    except Exception:
        return Response({'detail':'شعبه معتبر یا مجاز نیست'},status=403)
    return Response(_ready_notification_capabilities(branch))

@api_view(["POST"])
@transaction.atomic
def checkout(request):
    from apps.accounts.override import validate_override
    if not has_perm(request.user,'orders.create'):
        return Response({"detail":"دسترسی ثبت سفارش ندارید"},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get("branch"))
    except Exception:
        return Response({"detail":"شعبه سفارش معتبر یا مجاز نیست"},status=403)

    method=request.data.get("ready_notification_method","NONE") if request.data.get("order_type","TAKEAWAY")=="TAKEAWAY" else "NONE"
    if method not in ("NONE","SMS","PAGER"):
        return Response({'detail':'روش اعلان معتبر نیست'},status=400)
    notification_caps=_ready_notification_capabilities(branch)
    if method=="SMS" and (not notification_caps['sms'] or not request.data.get("customer_phone")):
        return Response({'detail':'پیامک این شعبه فعال نیست یا شماره مشتری وارد نشده است'},status=400)
    pager=None
    if method=="PAGER":
        if not notification_caps['pager']:
            return Response({'detail':'پیجر برای این شعبه فعال و آماده نیست'},status=400)
        pager=PagerDevice.objects.filter(pk=request.data.get('pager_id'),branch=branch,status='AVAILABLE').first()
        if pager is None:
            return Response({'detail':'پیجر آزاد و معتبر انتخاب کنید'},status=400)

    rows=[]
    for raw in request.data.get("items",[]):
        product=get_object_or_404(Product,pk=raw.get("product"),branch=branch,is_available=True)
        rows.append({"product":product,"quantity":raw.get("quantity",1),"notes":raw.get("notes","")})

    table_session=None
    if request.data.get("table"):
        table=get_object_or_404(
            Table.objects.select_related("hall__branch"),
            pk=request.data["table"],hall__branch=branch
        )
        try:
            table_session=get_or_open_table_session(
                table=table,branch=branch,user=request.user
            )
        except ValueError as e:
            return Response({"detail":str(e)},status=409)
    elif request.data.get("table_session"):
        table_session=get_object_or_404(
            TableSession.objects.select_related("table__hall__branch"),
            pk=request.data["table_session"],is_open=True,table__hall__branch=branch
        )

    manual=request.data.get("manual_discount")
    manager=None
    if manual:
        if has_perm(request.user,'discount.manual'):
            manager=request.user
        else:
            manager=validate_override(
                request.headers.get('X-Cafino-Override'),branch=branch,permission_code='discount.manual'
            )
            if not manager:
                return Response({"detail":"برای تخفیف دستی تأیید مدیر لازم است"},status=403)
    elif request.headers.get('X-Cafino-Override'):
        manager=validate_override(
            request.headers.get('X-Cafino-Override'),branch=branch,permission_code='discount.manual'
        )

    customer=None
    if request.data.get("customer_phone"):
        customer,_=Customer.objects.get_or_create(
            branch=branch,phone=request.data.get("customer_phone"),
            defaults={"name":request.data.get("customer_name") or request.data.get("customer_phone"),"is_walk_in":False}
        )
        if request.data.get("customer_name") and customer.name!=request.data.get("customer_name"):
            customer.name=request.data.get("customer_name")
            customer.save(update_fields=["name","updated_at"])

    delivery_fee=Decimal('0')
    delivery_address=None
    if request.data.get("order_type")=="DELIVERY":
        payload=request.data.get("delivery") or {}
        try:
            zone=DeliveryZone.objects.get(branch=branch,code=payload.get("zone_code"),is_active=True)
            subtotal=sum(
                (Decimal(row["product"].price)*Decimal(str(row.get("quantity",1))) for row in rows),
                Decimal('0')
            )
            delivery_fee=delivery_quote(zone,subtotal)
            if not payload.get("address"):
                return Response({"detail":"آدرس ارسال لازم است"},status=400)
            delivery_address=DeliveryAddress.objects.create(
                customer=customer,branch=branch,zone=zone,
                recipient_name=payload.get("recipient_name") or request.data.get("customer_name") or request.data.get("customer_phone") or "مشتری",
                phone=payload.get("phone") or request.data.get("customer_phone",""),
                address=payload.get("address"),postal_code=payload.get("postal_code",""),
                notes=payload.get("notes","")
            )
        except DeliveryZone.DoesNotExist:
            return Response({"detail":"منطقه ارسال معتبر نیست"},status=400)
        except ValueError as e:
            return Response({"detail":str(e)},status=400)

    try:
        order=checkout_order(
            branch=branch,items=rows,order_type=request.data.get("order_type","TAKEAWAY"),
            payment_method=request.data.get("payment_method","POS"),
            payments=request.data.get("payments"),user=request.user,customer=customer,
            table_session=table_session,notes=request.data.get("notes",""),
            discount_code=request.data.get('discount_code'),manual_discount=manual,
            manager_approved_by=manager,
            idempotency_key=request.headers.get('Idempotency-Key') or request.data.get('idempotency_key'),
            defer_payment=bool(request.data.get('defer_payment',False)),delivery_fee=delivery_fee
        )
    except ValueError as e:
        return Response({"detail":str(e)},status=400)

    if order.order_type=="TAKEAWAY":
        TakeawayProfile.objects.get_or_create(
            order=order,
            defaults={
                "pickup_number":str(order.order_number),
                "customer_name":request.data.get("customer_name",""),
                "customer_phone":request.data.get("customer_phone",""),
                "ready_notification_method":method,
                "pager":pager,
            }
        )
    if order.order_type=="DELIVERY" and delivery_address:
        from apps.delivery.services import create_delivery_assignment
        create_delivery_assignment(order=order,address=delivery_address,fee=delivery_fee)
    return Response(OrderSerializer(order).data,status=status.HTTP_201_CREATED)

@api_view(["POST"])
def create_multi_purchase(request):
    if not has_perm(request.user,'purchasing.manage'):
        return Response({'detail':'اجازه ثبت خرید ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه خرید معتبر یا مجاز نیست'},status=403)

    supplier=get_object_or_404(Supplier,pk=request.data.get('supplier'),branch=branch)
    rows=[]
    for raw in request.data.get('items',[]):
        item=get_object_or_404(InventoryItem,pk=raw.get('inventory_item'),branch=branch)
        rows.append({
            'inventory_item':item,'quantity':raw.get('quantity'),'unit_cost':raw.get('unit_cost'),
            'lot_number':raw.get('lot_number',''),'expires_at':raw.get('expires_at')
        })
    try:
        obj=create_purchase(
            branch=branch,supplier=supplier,rows=rows,invoice_date=request.data.get('invoice_date'),
            user=request.user,invoice_number=request.data.get('invoice_number',''),
            notes=request.data.get('notes',''),paid_amount=request.data.get('paid_amount',0),
            payment_method=request.data.get('payment_method','CASH')
        )
    except ValueError as e:
        return Response({'detail':str(e)},status=400)
    return Response(PurchaseInvoiceSerializer(obj).data,status=201)

@api_view(["GET"])
def financial_report(request):
    if not has_perm(request.user,'reports.view'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.query_params.get("branch"))
    except Exception:
        return Response({'detail':'شعبه گزارش معتبر یا مجاز نیست'},status=403)
    return Response(profit_report(branch,request.query_params.get("start"),request.query_params.get("end")))

@api_view(['POST'])
def request_approval(request):
    typ=request.data.get('request_type')
    required='discount.request' if typ==ApprovalRequest.Type.DISCOUNT else 'void.request'
    if typ not in [ApprovalRequest.Type.DISCOUNT,ApprovalRequest.Type.VOID]:
        return Response({'detail':'نوع درخواست نامعتبر'},status=400)
    if not has_perm(request.user,required):
        return Response({'detail':'اجازه ثبت این درخواست را ندارید'},status=403)
    order=get_object_or_404(Order.objects.select_related('branch'),pk=request.data['order'])
    if not can_access_branch(request.user,order.branch):
        return Response({'detail':'دسترسی به سفارش ندارید'},status=403)
    a=ApprovalRequest.objects.create(
        order=order,request_type=typ,requested_by=request.user,
        amount=request.data.get('amount',0) or 0,percent=request.data.get('percent',0) or 0,
        reason=request.data.get('reason','')
    )
    log_action(actor=request.user,branch=order.branch,action='APPROVAL_REQUESTED',entity=a,description=a.reason,request=request)
    return Response(ApprovalRequestSerializer(a).data,status=201)

@api_view(['POST'])
def daily_close(request):
    if not has_perm(request.user,'daily_close.execute'):
        return Response({'detail':'اجازه بستن روز مالی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه معتبر یا مجاز نیست'},status=403)
    try:
        obj=close_business_day(
            branch=branch,business_date=request.data.get('business_date') or timezone.localdate(),
            counted_cash=request.data.get('counted_cash',0),user=request.user
        )
        return Response(DailyClosingSerializer(obj).data,status=201)
    except ValueError as e:
        return Response({'detail':str(e)},status=409)

@api_view(['GET'])
def sales_reports(request):
    if not has_perm(request.user,'reports.view'):
        return Response({'detail':'اجازه مشاهده گزارش ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.query_params.get('branch'))
    except Exception:
        return Response({'detail':'شعبه گزارش معتبر یا مجاز نیست'},status=403)
    return Response(sales_analytics(branch,request.GET.get('start'),request.GET.get('end')))



@api_view(['POST'])
@transaction.atomic
def settings_user_create(request):
    if not has_perm(request.user,'permissions.manage'):
        return Response({'detail':'دسترسی مدیریت کاربران ندارید'},status=403)
    business=tenant_business(request.user)
    if request.user.is_superuser and request.data.get('business'):
        business=get_object_or_404(Business,pk=request.data.get('business'))
    if business is None:
        return Response({'detail':'کسب‌وکار کاربر مشخص نیست'},status=400)
    username=str(request.data.get('username') or '').strip()
    password=str(request.data.get('password') or '')
    role=request.data.get('role') or User.Role.CASHIER
    if not username or len(username)<3:
        return Response({'detail':'نام کاربری حداقل سه کاراکتر باشد'},status=400)
    if len(password)<8:
        return Response({'detail':'رمز عبور حداقل هشت کاراکتر باشد'},status=400)
    if role not in dict(User.Role.choices):
        return Response({'detail':'نقش نامعتبر است'},status=400)
    if not request.user.is_superuser and request.user.role!=User.Role.OWNER and role==User.Role.OWNER:
        return Response({'detail':'فقط مالک می‌تواند کاربر با نقش مالک بسازد'},status=403)
    if User.objects.filter(username=username).exists():
        return Response({'detail':'این نام کاربری قبلاً استفاده شده است'},status=409)
    branch=None
    if request.data.get('branch'):
        branch=get_object_or_404(Branch.objects.select_related('business'),pk=request.data.get('branch'))
        if branch.business_id!=business.id:
            return Response({'detail':'شعبه متعلق به کسب‌وکار نیست'},status=400)
        if not request.user.is_superuser:
            assert_branch_access(request.user,branch)
    if role in User.OPERATIONAL_ROLES and branch is None:
        return Response({'detail':'نقش عملیاتی باید شعبه داشته باشد'},status=400)
    user=User(
        username=username,first_name=str(request.data.get('first_name') or '').strip(),
        last_name=str(request.data.get('last_name') or '').strip(),email=str(request.data.get('email') or '').strip(),
        role=role,business=business,branch=branch,is_active=True
    )
    user.set_password(password)
    user.save()
    log_action(
        actor=request.user,branch=branch,action='TEAM_USER_CREATED',entity=user,
        after={'username':user.username,'role':user.role,'business':business.id,'branch':branch.id if branch else None},request=request
    )
    return Response(UserManagementSerializer(user).data,status=201)


@api_view(['POST'])
@transaction.atomic
def settings_user_password(request,user_id):
    if not has_perm(request.user,'permissions.manage'):
        return Response({'detail':'دسترسی مدیریت کاربران ندارید'},status=403)
    target=get_object_or_404(User.objects.select_related('business','branch'),pk=user_id)
    if not request.user.is_superuser:
        business=tenant_business(request.user)
        if business is None or target.business_id!=business.id:
            return Response({'detail':'دسترسی به این کاربر ندارید'},status=403)
        if request.user.role!=User.Role.OWNER and target.role==User.Role.OWNER:
            return Response({'detail':'فقط مالک می‌تواند رمز مالک را تغییر دهد'},status=403)
    password=str(request.data.get('password') or '')
    if len(password)<8:
        return Response({'detail':'رمز عبور حداقل هشت کاراکتر باشد'},status=400)
    target.set_password(password)
    target.save(update_fields=['password'])
    log_action(actor=request.user,branch=target.branch,action='TEAM_PASSWORD_RESET',entity=target,request=request)
    return Response({'ok':True})

@api_view(['GET'])
def settings_context(request):
    if not has_perm(request.user,'settings.manage'):
        return Response({'detail':'دسترسی به تنظیمات ندارید'},status=403)
    if request.user.is_superuser:
        business=(request.user.business if request.user.business_id else None)
        if request.query_params.get('business'):
            business=get_object_or_404(Business,pk=request.query_params.get('business'))
    else:
        business=tenant_business(request.user)
    if business is None:
        return Response({'detail':'کسب‌وکار برای تنظیمات مشخص نیست'},status=400)
    branches=Branch.objects.filter(business=business).order_by('name')
    modules=BusinessModule.objects.filter(business=business).order_by('key')
    permissions_map={code:has_perm(request.user,code) for code in ALL_PERMISSION_CODES}
    return Response({
        'business':BusinessSerializer(business).data,
        'branches':BranchSerializer(branches,many=True).data,
        'modules':BusinessModuleSerializer(modules,many=True).data,
        'permissions':permissions_map,
        'current_branch':request.user.branch_id,
        'role':request.user.role,
    })

@api_view(['GET'])
def permissions_me(request):
    return Response({'role':request.user.role,'permissions':{c:has_perm(request.user,c) for c in ALL_PERMISSION_CODES}})

@api_view(['GET'])
def permission_matrix(request):
    if not has_perm(request.user,'permissions.manage'):return Response({'detail':'دسترسی ندارید'},status=403)
    return Response({'groups':PERMISSION_GROUPS,'roles':User.Role.choices,'role_permissions':{k:list(v) for k,v in ROLE_PERMISSIONS.items()}})

@api_view(['POST'])
def manager_pin_set(request):
    if not has_perm(request.user,'manager_pin.manage'):return Response({'detail':'دسترسی ندارید'},status=403)
    try:set_manager_pin(request.user,request.data.get('pin'))
    except ValueError as e:return Response({'detail':str(e)},status=400)
    log_action(actor=request.user,branch=request.user.branch,action='MANAGER_PIN_UPDATED',entity=request.user,request=request)
    return Response({'ok':True})

@api_view(['POST'])
def manager_override(request):
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه Override معتبر یا مجاز نیست'},status=403)
    permission_code=request.data.get('permission_code')
    if permission_code not in {'discount.manual','orders.void','payments.refund'}:
        return Response({'detail':'این عملیات Override‌پذیر نیست'},status=400)
    try:
        token,manager=issue_override(
            branch=branch,pin=request.data.get('pin'),permission_code=permission_code
        )
    except ValueError:
        return Response({'detail':'PIN مدیر یا سطح دسترسی معتبر نیست'},status=403)
    log_action(
        actor=manager,branch=branch,action='MANAGER_OVERRIDE_ISSUED',
        entity=manager,description=permission_code,request=request
    )
    return Response({
        'token':token,'expires_in':120,
        'manager':manager.get_full_name() or manager.username
    })


@api_view(['POST'])
def attendance_clock_in(request):
    if not has_perm(request.user,'workforce.clock'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    if not request.user.branch_id:
        return Response({'detail':'ثبت حضور برای کاربر بدون شعبه مجاز نیست'},status=400)
    try:
        attendance=clock_in(request.user,request.user.branch)
    except ValueError as e:
        return Response({'detail':str(e)},status=409)
    return Response(AttendanceSerializer(attendance).data,status=201)

@api_view(['POST'])
def attendance_clock_out(request):
    if not has_perm(request.user,'workforce.clock'):return Response({'detail':'دسترسی ندارید'},status=403)
    try:a=clock_out(request.user)
    except ValueError as e:return Response({'detail':str(e)},status=409)
    return Response(AttendanceSerializer(a).data)

@api_view(['POST'])
def waste_create(request):
    if not has_perm(request.user,'waste.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    item=get_object_or_404(InventoryItem.objects.select_related('branch'),pk=request.data.get('item'))
    cross='inventory.transfer' if has_perm(request.user,'inventory.transfer') else 'branches.dashboard'
    if not can_access_branch(request.user,item.branch,cross_permission=cross):
        return Response({'detail':'دسترسی به انبار این شعبه ندارید'},status=403)
    try:
        record=record_waste(
            item=item,quantity=request.data.get('quantity'),reason=request.data.get('reason','ضایعات'),
            note=request.data.get('note',''),user=request.user
        )
    except ValueError as e:
        return Response({'detail':str(e)},status=400)
    return Response(WasteRecordSerializer(record).data,status=201)

@api_view(['GET'])
def food_cost(request):
    if not has_perm(request.user,'food_cost.view'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.query_params.get('branch'))
    except Exception:
        return Response({'detail':'شعبه گزارش معتبر یا مجاز نیست'},status=403)
    today=timezone.localdate()
    start=request.query_params.get('start') or str(today.replace(day=1))
    end=request.query_params.get('end') or str(today)
    return Response(food_cost_report(branch,start,end))

@api_view(['GET'])
def branches_dashboard(request):
    if not has_perm(request.user,'branches.dashboard'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    if request.user.is_superuser and request.query_params.get('business'):
        business=get_object_or_404(Business,pk=request.query_params.get('business'))
    else:
        business=tenant_business(request.user)
    if business is None:
        return Response({'detail':'کسب‌وکار برای داشبورد مشخص نیست'},status=400)
    return Response(multi_branch_dashboard(business))

@api_view(['POST'])
def inventory_count_create(request):
    if not has_perm(request.user,'inventory.count'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه شمارش معتبر یا مجاز نیست'},status=403)
    rows=[]
    for raw in request.data.get('lines',[]):
        item=get_object_or_404(InventoryItem,pk=raw.get('item'),branch=branch)
        rows.append({'item':item,'counted_quantity':raw.get('counted_quantity')})
    try:
        obj=create_inventory_count(
            branch=branch,title=request.data.get('title','شمارش انبار'),
            lines=rows,user=request.user,notes=request.data.get('notes','')
        )
    except ValueError as e:
        return Response({'detail':str(e)},status=400)
    return Response(InventoryCountSerializer(obj).data,status=201)

@api_view(['POST'])
@transaction.atomic
def stock_transfer_create(request):
    if not has_perm(request.user,'inventory.transfer'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    source=get_object_or_404(Branch.objects.select_related('business'),pk=request.data.get('source_branch'))
    dest=get_object_or_404(Branch.objects.select_related('business'),pk=request.data.get('destination_branch'))
    if source.id==dest.id:
        return Response({'detail':'شعبه مبدا و مقصد باید متفاوت باشند'},status=400)
    if source.business_id!=dest.business_id:
        return Response({'detail':'انتقال بین دو کسب‌وکار مجاز نیست'},status=400)
    try:
        assert_branch_access(request.user,source,cross_permission='inventory.transfer')
        assert_branch_access(request.user,dest,cross_permission='inventory.transfer')
    except Exception:
        return Response({'detail':'دسترسی انتقال برای این شعبه‌ها ندارید'},status=403)

    raw=request.data.get('lines',[])
    if not raw:
        return Response({'detail':'حداقل یک آیتم لازم است'},status=400)
    validated=[]
    try:
        for row in raw:
            src=get_object_or_404(InventoryItem,pk=row.get('source_item'),branch=source)
            dst=get_object_or_404(InventoryItem,pk=row.get('destination_item'),branch=dest)
            qty=Decimal(str(row.get('quantity')))
            if qty<=0:
                raise ValueError('مقدار انتقال نامعتبر است')
            validated.append((src,dst,qty))
    except (ValueError,TypeError) as e:
        return Response({'detail':str(e)},status=400)

    obj=StockTransfer.objects.create(
        source_branch=source,destination_branch=dest,requested_by=request.user,
        reference=request.data.get('reference',''),notes=request.data.get('notes','')
    )
    for src,dst,qty in validated:
        StockTransferLine.objects.create(
            transfer=obj,source_item=src,destination_item=dst,quantity=qty
        )
    return Response(StockTransferSerializer(obj).data,status=201)

@api_view(['POST'])
def order_settle(request,pk):
    order=get_object_or_404(Order.objects.select_related('branch'),pk=pk)
    if not can_access_branch(request.user,order.branch):
        return Response({'detail':'دسترسی به سفارش ندارید'},status=403)
    if order.status==Order.Status.CANCELLED:
        return Response({'detail':'سفارش لغوشده قابل تسویه نیست'},status=409)
    if not has_perm(request.user,'payments.create'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        payments=settle_order(order,payments=request.data.get('payments'),user=request.user,require_full=bool(request.data.get('require_full',True)))
    except ValueError as e:
        return Response({'detail':str(e)},status=400)
    return Response(PaymentSerializer(payments,many=True).data,status=201)

@api_view(['POST'])
def receipt_job_create(request,pk):
    if not has_perm(request.user,'printing.use'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    order=get_object_or_404(
        Order.objects.prefetch_related('items','payments').select_related(
            'branch__business','customer','table_session__table'
        ),pk=pk
    )
    if not can_access_branch(request.user,order.branch):
        return Response({'detail':'دسترسی به سفارش ندارید'},status=403)
    printer=None
    if request.data.get('printer'):
        printer=get_object_or_404(PrinterDevice,pk=request.data.get('printer'),branch=order.branch)
    job=create_receipt_job(order,printer=printer,user=request.user)
    return Response(PrintJobSerializer(job).data,status=201)


@api_view(['GET'])
def receipt_payload(request,pk):
    if not has_perm(request.user,'printing.use'):return Response({'detail':'دسترسی ندارید'},status=403)
    order=get_object_or_404(Order.objects.prefetch_related('items','payments').select_related('branch__business','customer','table_session__table'),pk=pk)
    if not _branch_accessible(request.user,order.branch):return Response({'detail':'دسترسی به سفارش ندارید'},status=403)
    return Response(order_receipt_payload(order))

@api_view(['GET'])
def kitchen_print_payload(request,pk):
    if not has_perm(request.user,'printing.use') and not has_perm(request.user,'kitchen.view'):return Response({'detail':'دسترسی ندارید'},status=403)
    ticket=get_object_or_404(KitchenTicket.objects.select_related('order__branch','order__table_session__table','station').prefetch_related('order__items'),pk=pk)
    if not _branch_accessible(request.user,ticket.order.branch):return Response({'detail':'دسترسی به تیکت ندارید'},status=403)
    return Response(kitchen_ticket_payload(ticket))

@api_view(['POST'])
def kitchen_job_create(request,pk):
    if not has_perm(request.user,'printing.use') and not has_perm(request.user,'kitchen.view'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    ticket=get_object_or_404(
        KitchenTicket.objects.select_related(
            'order__branch','order__table_session__table','station'
        ).prefetch_related('order__items'),pk=pk
    )
    if not can_access_branch(request.user,ticket.order.branch):
        return Response({'detail':'دسترسی به تیکت ندارید'},status=403)
    printer=None
    if request.data.get('printer'):
        printer=get_object_or_404(
            PrinterDevice,pk=request.data.get('printer'),branch=ticket.order.branch
        )
    job=create_kitchen_job(ticket,printer=printer,user=request.user)
    return Response(PrintJobSerializer(job).data,status=201)


@api_view(['GET'])
def kpi_report(request):
    if not has_perm(request.user,'reports.view'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.query_params.get('branch'))
    except Exception:
        return Response({'detail':'شعبه گزارش معتبر یا مجاز نیست'},status=403)
    return Response(management_kpis(branch,request.query_params.get('start'),request.query_params.get('end')))

@api_view(['POST'])
def bill_split_create(request,pk):
    if not has_perm(request.user,'payments.split'):return Response({'detail':'دسترسی ندارید'},status=403)
    order=get_object_or_404(Order,pk=pk)
    if not _branch_accessible(request.user,order.branch):return Response({'detail':'دسترسی ندارید'},status=403)
    try:rows=create_item_splits(order,request.data.get('groups',[]))
    except ValueError as e:return Response({'detail':str(e)},status=400)
    return Response(BillSplitSerializer(rows,many=True).data,status=201)

@api_view(['POST'])
def loyalty_redeem(request,customer_id):
    if not has_perm(request.user,'loyalty.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    customer=get_object_or_404(Customer.objects.select_related('branch'),pk=customer_id)
    if not can_access_branch(request.user,customer.branch):
        return Response({'detail':'دسترسی به مشتری ندارید'},status=403)
    try:
        wallet=redeem_points_to_wallet(customer,request.data.get('points'))
    except ValueError as e:
        return Response({'detail':str(e)},status=400)
    log_action(
        actor=request.user,branch=customer.branch,action='LOYALTY_REDEEMED',entity=customer,
        after={'points':request.data.get('points'),'wallet_balance':str(wallet.balance)},request=request
    )
    return Response(WalletAccountSerializer(wallet).data)

@api_view(['POST'])
def wallet_credit(request,customer_id):
    if not has_perm(request.user,'loyalty.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    customer=get_object_or_404(Customer.objects.select_related('branch'),pk=customer_id)
    if not can_access_branch(request.user,customer.branch):
        return Response({'detail':'دسترسی به مشتری ندارید'},status=403)
    try:
        wallet=credit_wallet(
            customer,request.data.get('amount'),reference=request.data.get('reference',''),
            note=request.data.get('note','')
        )
    except ValueError as e:
        return Response({'detail':str(e)},status=400)
    log_action(
        actor=request.user,branch=customer.branch,action='WALLET_CREDITED',entity=customer,
        after={'amount':request.data.get('amount'),'wallet_balance':str(wallet.balance)},request=request
    )
    return Response(WalletAccountSerializer(wallet).data)

@api_view(['POST'])
def process_notifications_api(request):
    if not has_perm(request.user,'notifications.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    limit=min(max(int(request.data.get('limit',50)),1),100)
    if request.user.is_superuser and request.data.get('branch'):
        branch=get_object_or_404(Branch,pk=request.data.get('branch'))
        rows=process_pending(branch=branch,limit=limit)
    elif request.user.branch_id:
        rows=process_pending(branch=request.user.branch,limit=limit)
    else:
        business=tenant_business(request.user)
        if business is None:
            return Response({'detail':'کسب‌وکار مشخص نیست'},status=400)
        rows=process_pending(business=business,limit=limit)
    return Response(NotificationSerializer(rows,many=True).data)

@api_view(['POST'])
def online_settings_ensure(request):
    if not has_perm(request.user,'online_ordering.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه معتبر یا مجاز نیست'},status=403)
    return Response(OnlineMenuSettingsSerializer(ensure_settings(branch)).data)

@api_view(['POST'])
def table_qr_ensure(request,pk):
    if not has_perm(request.user,'online_ordering.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    table=get_object_or_404(Table.objects.select_related('hall__branch'),pk=pk)
    if not can_access_branch(request.user,table.hall.branch):
        return Response({'detail':'دسترسی به میز ندارید'},status=403)
    token,_=TableQrToken.objects.get_or_create(table=table)
    return Response(TableQrTokenSerializer(token).data)

@api_view(['GET'])
def table_qr_svg(request,pk):
    if not has_perm(request.user,'online_ordering.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    import io
    import qrcode
    import qrcode.image.svg

    table=get_object_or_404(Table.objects.select_related('hall__branch'),pk=pk)
    if not can_access_branch(request.user,table.hall.branch):
        return Response({'detail':'دسترسی به میز ندارید'},status=403)
    qr,_=TableQrToken.objects.get_or_create(table=table)
    settings=ensure_settings(table.hall.branch)
    base=(settings.public_base_url or 'http://127.0.0.1:3000').rstrip('/')
    url=f'{base}/menu/{settings.public_slug}?table={qr.token}'
    img=qrcode.make(url,image_factory=qrcode.image.svg.SvgPathImage)
    buf=io.BytesIO()
    img.save(buf)
    return HttpResponse(buf.getvalue(),content_type='image/svg+xml')


@api_view(['POST'])
def gift_card_issue(request):
    if not has_perm(request.user,'giftcards.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه معتبر یا مجاز نیست'},status=403)
    try:
        card,code=issue_card(
            branch=branch,amount=request.data.get('amount'),
            expires_at=request.data.get('expires_at') or None,
            purchaser_name=request.data.get('purchaser_name',''),
            recipient_name=request.data.get('recipient_name',''),note=request.data.get('note','')
        )
    except ValueError as e:
        return Response({'detail':str(e)},status=400)
    data=GiftCardSerializer(card).data
    data['code']=code
    log_action(
        actor=request.user,branch=branch,action='GIFT_CARD_ISSUED',entity=card,
        after={'amount':str(card.initial_balance)},request=request
    )
    return Response(data,status=201)

@api_view(['POST'])
def gift_card_balance(request):
    if not (has_perm(request.user,'giftcards.manage') or has_perm(request.user,'payments.create')):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه معتبر یا مجاز نیست'},status=403)
    try:
        card=find_card(branch,request.data.get('code'))
    except ValueError:
        return Response({'detail':'کارت هدیه معتبر نیست'},status=404)
    return Response({
        'masked_code':f'****-{card.code_last4}','balance':card.balance,'expires_at':card.expires_at
    })

@api_view(['POST'])
def lot_count_create(request):
    if not has_perm(request.user,'inventory.lot_count'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه شمارش معتبر یا مجاز نیست'},status=403)
    lines=[]
    for row in request.data.get('lines',[]):
        lot=get_object_or_404(InventoryLot.objects.select_related('item'),pk=row.get('lot'),item__branch=branch)
        lines.append({'lot':lot,'counted_quantity':row.get('counted_quantity')})
    try:
        count=create_lot_count(
            branch=branch,title=request.data.get('title','شمارش Lot'),lines=lines,
            user=request.user,notes=request.data.get('notes','')
        )
    except ValueError as e:
        return Response({'detail':str(e)},status=400)
    return Response(LotInventoryCountSerializer(count).data,status=201)

@api_view(['POST'])
def order_items_transfer(request,pk):
    if not has_perm(request.user,'orders.transfer'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    src=get_object_or_404(Order.objects.select_related('branch'),pk=pk)
    dst=get_object_or_404(Order.objects.select_related('branch'),pk=request.data.get('destination_order'))
    if not can_access_branch(request.user,src.branch) or not can_access_branch(request.user,dst.branch):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        source,destination=transfer_order_items(
            source_order=src,destination_order=dst,lines=request.data.get('lines',[]),user=request.user
        )
    except ValueError as e:
        return Response({'detail':str(e)},status=409)
    return Response({
        'source':OrderSerializer(source).data,'destination':OrderSerializer(destination).data
    })

@api_view(['POST'])
def table_session_transfer(request,pk):
    if not has_perm(request.user,'tables.use'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    session=get_object_or_404(TableSession.objects.select_related('table__hall__branch'),pk=pk,is_open=True)
    table=get_object_or_404(Table.objects.select_related('hall__branch'),pk=request.data.get('table'))
    if not can_access_branch(request.user,session.table.hall.branch) or not can_access_branch(request.user,table.hall.branch):
        return Response({'detail':'دسترسی به میز یا Session ندارید'},status=403)
    try:
        result=transfer_table_session(session,table,user=request.user)
    except ValueError as e:
        return Response({'detail':str(e)},status=409)
    return Response(TableSessionSerializer(result).data)

@api_view(['POST'])
def push_generate_keys(request):
    if not has_perm(request.user,'notifications.manage'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    import base64
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه معتبر یا مجاز نیست'},status=403)
    private=ec.generate_private_key(ec.SECP256R1())
    private_pem=private.private_bytes(
        serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()
    ).decode()
    public_bytes=private.public_key().public_bytes(
        serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint
    )
    public_key=base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')
    cfg,_=PushProviderConfig.objects.get_or_create(branch=branch)
    cfg.vapid_public_key=public_key
    cfg.set_private_key(private_pem)
    cfg.subject=request.data.get('subject') or cfg.subject
    cfg.is_active=True
    cfg.save(update_fields=['vapid_public_key','vapid_private_key_encrypted','subject','is_active','updated_at'])
    return Response(PushProviderConfigSerializer(cfg).data)

@api_view(['POST'])
def checkout_preview(request):
    from apps.discounts.services import find_best_discount
    from apps.accounting.pricing import calculate_fiscal_totals
    from apps.accounts.override import validate_override

    if not has_perm(request.user,'orders.create'):
        return Response({'detail':'دسترسی ثبت/پیش‌نمایش سفارش ندارید'},status=403)
    try:
        branch=resolve_branch_for_user(request.user,request.data.get('branch'))
    except Exception:
        return Response({'detail':'شعبه سفارش معتبر یا مجاز نیست'},status=403)

    rows=[];subtotal=Decimal('0')
    for row in request.data.get('items',[]):
        product=get_object_or_404(Product,pk=row.get('product'),branch=branch,is_available=True)
        qty=Decimal(str(row.get('quantity',1)))
        if qty<=0:
            return Response({'detail':'تعداد نامعتبر است'},status=400)
        line=Decimal(product.price)*qty
        rows.append({'product':product,'line_total':line})
        subtotal+=line

    manager=request.user if has_perm(request.user,'discount.manual') else validate_override(
        request.headers.get('X-Cafino-Override'),branch=branch,permission_code='discount.manual'
    )
    discount=Decimal('0');rule=None;requires_manager=False
    manual=request.data.get('manual_discount')
    if manual:
        if not manager:
            return Response(
                {'detail':'برای Preview تخفیف دستی PIN مدیر لازم است','requires_manager':True},
                status=403
            )
        amount=Decimal(str(manual.get('amount') or 0))
        percent=Decimal(str(manual.get('percent') or 0))
        if amount<0 or percent<0 or percent>100:
            return Response({'detail':'تخفیف نامعتبر است'},status=400)
        discount=min(
            subtotal,amount if amount else subtotal*percent/Decimal('100')
        )
    else:
        code=request.data.get('discount_code')
        rule,discount=find_best_discount(
            branch=branch,subtotal=subtotal,lines=rows,code=code,
            allow_manager_rules=bool(manager)
        )
        if code and not rule:
            privileged,_=find_best_discount(
                branch=branch,subtotal=subtotal,lines=rows,code=code,
                allow_manager_rules=True
            )
            if privileged and privileged.requires_manager:
                requires_manager=True
            else:
                return Response({'detail':'کد تخفیف معتبر نیست'},status=400)

    delivery_fee=Decimal('0')
    if request.data.get('order_type')=='DELIVERY':
        try:
            zone=DeliveryZone.objects.get(
                branch=branch,code=request.data.get('zone_code'),is_active=True
            )
            delivery_fee=delivery_quote(zone,subtotal)
        except DeliveryZone.DoesNotExist:
            return Response({'detail':'منطقه ارسال معتبر نیست'},status=400)
        except ValueError as e:
            return Response({'detail':str(e)},status=400)

    fiscal=calculate_fiscal_totals(
        branch=branch,order_type=request.data.get('order_type','TAKEAWAY'),
        subtotal=subtotal,discount=discount,delivery_fee=delivery_fee
    )
    return Response({
        'subtotal':subtotal,'discount_total':discount,
        'discount_rule':rule.name if rule else None,
        'requires_manager':requires_manager,**fiscal
    })
