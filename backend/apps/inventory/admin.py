from django.contrib import admin
from .models import (
    InventoryItem,StockMovement,RecipeItem,WasteRecord,
    InventoryCount,InventoryCountLine,StockTransfer,StockTransferLine,
    InventoryLot,LotInventoryCount,LotInventoryCountLine,
)
for model in [
    InventoryItem,StockMovement,RecipeItem,WasteRecord,
    InventoryCount,InventoryCountLine,StockTransfer,StockTransferLine,
    InventoryLot,LotInventoryCount,LotInventoryCountLine,
]:
    try: admin.site.register(model)
    except admin.sites.AlreadyRegistered: pass
