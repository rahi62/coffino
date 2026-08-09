from django.contrib import admin
from .models import (
    LoyaltyProgram,CustomerLoyaltyAccount,LoyaltyLedger,WalletAccount,WalletTransaction,
    LoyaltyTier,LoyaltyCampaign,
)
for model in [
    LoyaltyProgram,CustomerLoyaltyAccount,LoyaltyLedger,WalletAccount,WalletTransaction,
    LoyaltyTier,LoyaltyCampaign,
]:
    try: admin.site.register(model)
    except admin.sites.AlreadyRegistered: pass
