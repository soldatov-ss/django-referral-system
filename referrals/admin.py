from django.contrib import admin

from referrals.models import ReferralProgram, PayoutMethod, Referral, Promoter, PromoterCommission, \
    PromoterPayout


@admin.register(ReferralProgram)
class ReferralProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "commission_rate", "is_active", "id")


@admin.register(PayoutMethod)
class PayoutMethodAdmin(admin.ModelAdmin):
    list_display = ("method", "payment_address")


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        "user",
        "promoter",
    )
    list_display = (
        "id",
        "user",
        "promoter",
        "invitation_method",
        "status",
    )
    search_fields = ("id",)
    list_filter = ("status", "invitation_method", "id")


@admin.register(Promoter)
class PromoterAdmin(admin.ModelAdmin):
    autocomplete_fields = ("user",)
    search_fields = ("user__email",)
    list_display = ("referral_link", "referral_token", "user", "id")


@admin.register(PromoterCommission)
class PromoterCommissionAdmin(admin.ModelAdmin):
    search_fields = ("promoter__user__email",)
    list_display = ("promoter", "referral", "amount", "status")
    list_filter = ("status", "amount")


@admin.register(PromoterPayout)
class PromoterPayoutsAdmin(admin.ModelAdmin):
    search_fields = ("promoter_user_email",)
    list_display = ("promoter", "amount", "payout_method", "created")
    list_filter = ("payout_method",)
