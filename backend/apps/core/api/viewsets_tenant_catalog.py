from rest_framework.response import Response

from apps.orders.models import OrderItem

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

class CategoryVS(BaseVS):
    queryset=Category.objects.all()
    serializer_class=CategorySerializer
    cafino_write_permission='inventory.manage'
    cafino_read_permission=('orders.create', 'inventory.view', 'inventory.manage')
    cafino_allow_destroy=True

    def destroy(self,request,*args,**kwargs):
        category=self.get_object()
        if category.products.exists():
            return Response({'detail':'این دسته‌بندی به محصول متصل است؛ ابتدا محصولات را به دستهٔ دیگری منتقل یا حذف کنید.'},status=400)
        if DiscountRule.objects.filter(category=category).exists():
            return Response({'detail':'این دسته‌بندی در قانون تخفیف استفاده شده است؛ ابتدا قانون وابسته را ویرایش یا حذف کنید.'},status=400)
        return super().destroy(request,*args,**kwargs)

class ProductVS(BaseVS):
    cafino_read_permission=('orders.create', 'inventory.view', 'inventory.manage')
    cafino_write_permission='inventory.manage'
    cafino_allow_destroy=True
    queryset=Product.objects.select_related("category","preparation_station").all(); serializer_class=ProductSerializer
    filterset_fields=["branch","category","is_available"]; search_fields=["name","sku"]

    def destroy(self,request,*args,**kwargs):
        product=self.get_object()
        if OrderItem.objects.filter(product=product).exists():
            return Response({'detail':'این محصول در سفارش ثبت شده و برای حفظ سابقه قابل حذف نیست. می‌توانید آن را غیرفعال کنید.'},status=400)
        if DiscountRule.objects.filter(product=product).exists():
            return Response({'detail':'این محصول در قانون تخفیف استفاده شده است؛ ابتدا قانون وابسته را ویرایش یا حذف کنید.'},status=400)
        return super().destroy(request,*args,**kwargs)

class CustomerVS(BaseVS): queryset=Customer.objects.all(); serializer_class=CustomerSerializer; search_fields=["name","phone"]; cafino_write_permission='orders.create'; cafino_read_permission=('orders.view', 'orders.create', 'loyalty.manage')
