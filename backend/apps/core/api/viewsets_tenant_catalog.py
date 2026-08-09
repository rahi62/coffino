from .shared import *
from .shared import BaseVS, _branch_accessible

class BusinessVS(BaseVS):
    queryset=Business.objects.all()
    serializer_class=BusinessSerializer
    cafino_write_permission='business.manage'

    def create(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({'detail':'ایجاد Business جدید فقط برای Platform Admin مجاز است'},status=403)
        return super().create(request,*args,**kwargs)

class BranchVS(BaseVS): queryset=Branch.objects.all(); serializer_class=BranchSerializer; cafino_write_permission='branches.manage'

class BusinessModuleVS(BaseVS): queryset=BusinessModule.objects.all(); serializer_class=BusinessModuleSerializer; cafino_write_permission='business.manage'; cafino_read_permission='business.manage'

class CategoryVS(BaseVS): queryset=Category.objects.all(); serializer_class=CategorySerializer; cafino_write_permission='inventory.manage'; cafino_read_permission=('orders.create', 'inventory.view', 'inventory.manage')

class ProductVS(BaseVS):
    cafino_read_permission=('orders.create', 'inventory.view', 'inventory.manage')
    cafino_write_permission='inventory.manage'
    queryset=Product.objects.select_related("category","preparation_station").all(); serializer_class=ProductSerializer
    filterset_fields=["branch","category","is_available"]; search_fields=["name","sku"]

class CustomerVS(BaseVS): queryset=Customer.objects.all(); serializer_class=CustomerSerializer; search_fields=["name","phone"]; cafino_write_permission='orders.create'; cafino_read_permission=('orders.view', 'orders.create', 'loyalty.manage')

