from .shared import *
from .shared import BaseVS, _branch_accessible

class InventoryItemVS(BaseVS):
    cafino_read_permission=('inventory.view', 'inventory.manage', 'purchasing.view', 'purchasing.manage', 'production.manage', 'food_cost.view')
    cafino_write_permission='inventory.manage'
    queryset=InventoryItem.objects.all()
    serializer_class=InventoryItemSerializer

class IngredientCategoryVS(BaseVS):
    cafino_read_permission=('inventory.view', 'inventory.manage', 'purchasing.view', 'purchasing.manage')
    cafino_write_permission='inventory.manage'
    cafino_allow_destroy=True
    queryset=IngredientCategory.objects.all()
    serializer_class=IngredientCategorySerializer

    def destroy(self,request,*args,**kwargs):
        category=self.get_object()
        if category.materials.exists():
            return Response({'detail':'این دسته به مادهٔ اولیه متصل است؛ ابتدا مواد را به دستهٔ دیگری منتقل کنید.'},status=400)
        return super().destroy(request,*args,**kwargs)

class StockMovementVS(BaseVS): queryset=StockMovement.objects.select_related("item").all(); serializer_class=StockMovementSerializer; cafino_read_permission=('inventory.view', 'food_cost.view')

class RecipeItemVS(BaseVS):
    cafino_read_permission=('inventory.view', 'inventory.manage', 'production.manage')
    cafino_write_permission='inventory.manage'
    queryset=RecipeItem.objects.select_related("product","inventory_item").all()
    serializer_class=RecipeItemSerializer

    @action(detail=False,methods=['put'],url_path='save-recipe')
    @transaction.atomic
    def save_recipe(self,request):
        """Create or update every material of a product recipe as one operation."""
        self._assert_write_permission()
        serializer=RecipeSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product=serializer.validated_data['product']
        ingredients=serializer.validated_data['ingredients']

        # The serializer checks consistency; these checks enforce the caller's tenant and branch scope.
        self._assert_write_scope({'product':product})
        assert_branch_access(request.user,product.branch,cross_permission=self._cross_permission('inventory.recipeitem'))

        product=Product.objects.select_for_update().select_related('branch').get(pk=product.pk)
        existing_rows=list(RecipeItem.objects.select_for_update().filter(product=product))
        existing_by_material={}
        duplicate_rows=[]
        for row in existing_rows:
            if row.inventory_item_id in existing_by_material:
                duplicate_rows.append(row.pk)
            else:
                existing_by_material[row.inventory_item_id]=row
        if duplicate_rows:
            RecipeItem.objects.filter(pk__in=duplicate_rows).delete()

        changed=False
        for ingredient in ingredients:
            item=ingredient['inventory_item']
            quantity=ingredient['quantity']
            row=existing_by_material.pop(item.id,None)
            if row is None:
                RecipeItem.objects.create(product=product,inventory_item=item,quantity=quantity)
                changed=True
            elif row.quantity!=quantity:
                row.quantity=quantity
                row.save(update_fields=['quantity','updated_at'])
                changed=True
        if existing_by_material:
            RecipeItem.objects.filter(pk__in=[row.pk for row in existing_by_material.values()]).delete()
            changed=True

        if changed or duplicate_rows:
            log_action(
                actor=request.user,branch=product.branch,action='CONFIG_UPDATED',entity=product,
                metadata={'model':'inventory.recipeitem','source':'recipe-editor','ingredient_count':len(ingredients)},request=request,
            )
        rows=RecipeItem.objects.select_related('product','inventory_item').filter(product=product).order_by('id')
        return Response(RecipeItemSerializer(rows,many=True).data)

class WasteRecordVS(viewsets.ReadOnlyModelViewSet):
    queryset=WasteRecord.objects.select_related('item','created_by','branch').all()
    serializer_class=WasteRecordSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=super().get_queryset()
        if not (has_perm(self.request.user,'food_cost.view') or has_perm(self.request.user,'waste.manage')):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

class InventoryCountVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=InventoryCountSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=InventoryCount.objects.prefetch_related('lines__item').select_related('branch','counted_by','posted_by').all()
        if not has_perm(self.request.user,'inventory.count'):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

    @action(detail=True,methods=['post'])
    def post_count(self,request,pk=None):
        if not has_perm(request.user,'inventory.count'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            obj=post_inventory_count(self.get_object(),user=request.user)
        except ValueError as e:
            return Response({'detail':str(e)},status=409)
        return Response(self.get_serializer(obj).data)

class StockTransferVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=StockTransferSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=StockTransfer.objects.prefetch_related(
            'lines__source_item','lines__destination_item'
        ).select_related('source_branch','destination_branch').all()
        if not has_perm(self.request.user,'inventory.transfer'):
            return qs.none()
        if self.request.user.is_superuser:
            return qs
        business=tenant_business(self.request.user)
        if business is None:
            return qs.none()
        # Transfer permission is explicitly cross-branch but never cross-business.
        return qs.filter(source_branch__business=business,destination_branch__business=business)

    @action(detail=True,methods=['post'])
    def post_transfer(self,request,pk=None):
        if not has_perm(request.user,'inventory.transfer'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            obj=post_stock_transfer(self.get_object(),user=request.user)
        except ValueError as e:
            return Response({'detail':str(e)},status=409)
        return Response(self.get_serializer(obj).data)

class ProductionFormulaVS(BaseVS):
    cafino_read_permission=('production.manage', 'inventory.view')
    cafino_write_permission='production.manage'
    queryset=ProductionFormula.objects.select_related('branch','output_item').prefetch_related('ingredients__inventory_item').all()
    serializer_class=ProductionFormulaSerializer

class ProductionFormulaItemVS(BaseVS):
    cafino_read_permission=('production.manage', 'inventory.view')
    cafino_write_permission='production.manage'
    queryset=ProductionFormulaItem.objects.select_related('formula__branch','inventory_item__branch').all()
    serializer_class=ProductionFormulaItemSerializer

class ProductionBatchVS(BaseVS):
    cafino_read_permission=('production.manage', 'inventory.view')
    cafino_write_permission='production.manage'
    queryset=ProductionBatch.objects.select_related(
        'branch','formula','formula__output_item'
    ).prefetch_related('ingredient_snapshots__inventory_item').all()
    serializer_class=ProductionBatchSerializer

    def perform_create(self,serializer):
        self._assert_write_permission()
        self._assert_write_scope(serializer.validated_data)
        serializer.save(created_by=self.request.user)

    @action(detail=True,methods=['post'])
    def post_batch(self,request,pk=None):
        if not has_perm(request.user,'production.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            obj=post_production_batch(self.get_object(),user=request.user)
        except ValueError as e:
            return Response({'detail':str(e)},status=409)
        return Response(self.get_serializer(obj).data)

class InventoryLotVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=InventoryLotSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=InventoryLot.objects.select_related('item','item__branch').all()
        if not has_perm(self.request.user,'inventory.view'):
            return qs.none()
        cross='inventory.transfer' if has_perm(self.request.user,'inventory.transfer') else 'branches.dashboard'
        return scope_queryset(
            qs,self.request.user,branch_path='item__branch',
            business_path='item__branch__business',cross_permission=cross
        )

    @action(detail=True,methods=['post'])
    def block(self,request,pk=None):
        if not has_perm(request.user,'inventory.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        x=self.get_object()
        x.is_blocked=bool(request.data.get('is_blocked',True))
        x.save(update_fields=['is_blocked','updated_at'])
        return Response(self.get_serializer(x).data)

class LotInventoryCountVS(viewsets.ReadOnlyModelViewSet):
    queryset=LotInventoryCount.objects.prefetch_related('lines__lot__item').select_related('branch').all()
    serializer_class=LotInventoryCountSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=super().get_queryset()
        if not has_perm(self.request.user,'inventory.lot_count'):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

    @action(detail=True,methods=['post'])
    def post_count(self,request,pk=None):
        if not has_perm(request.user,'inventory.lot_count'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            x=post_lot_count(self.get_object(),user=request.user)
        except ValueError as e:
            return Response({'detail':str(e)},status=409)
        return Response(self.get_serializer(x).data)
