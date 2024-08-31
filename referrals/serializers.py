from rest_framework import serializers

from referrals.models import (
    PayoutMethod,
    Promoter,
    PromoterCommission,
    PromoterPayout,
    Referral, ReferralProgram,
)
from referrals.repositories.promoter_commission_repository import promoter_commission_repository


class CamelCaseSerializer(serializers.ModelSerializer):

    def get_current_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {snake_case_to_camel_case(key): value for key, value in ret.items()}


def snake_case_to_camel_case(snake_case):
    components = snake_case.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class PromoterCommissionSerializer(CamelCaseSerializer):
    class Meta:
        model = PromoterCommission
        fields = "__all__"


class ReferralSerializer(CamelCaseSerializer):
    email = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    commission_amount = serializers.SerializerMethodField()
    commission_status = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = (
            "user_id",
            "email",
            "status",
            "invitation_method",
            "commission_rate",
            "commission_amount",
            "commission_status",
        )

    def get_email(self, obj):
        return obj.user.email

    def get_user_id(self, obj):
        return obj.user.id

    def get_commission_amount(self, obj):
        commission = promoter_commission_repository.get_referral_positive_commission(obj)
        if commission:
            return commission.amount
        return 0

    def get_commission_status(self, obj):
        commission = promoter_commission_repository.get_referral_positive_commission(obj)
        if commission:
            return commission.status
        return None


class PayoutMethodSerializer(CamelCaseSerializer):
    class Meta:
        model = PayoutMethod
        fields = ["method", "payment_address"]


class PromoterSerializer(CamelCaseSerializer):
    active_payout_method = PayoutMethodSerializer()
    commission_rate = serializers.SerializerMethodField()

    class Meta:
        model = Promoter
        fields = (
            "id",
            "user",
            "referral_token",
            "referral_link",
            "active_payout_method",
            "current_balance",
            "total_earned",
            "total_paid",
            "created",
            "updated",
            "link_clicked",
            "min_withdrawal_balance",
            "commission_rate",
        )

    def get_commission_rate(self, obj):
        active_program = ReferralProgram.get_active_referral_program()
        return active_program.commission_rate


class PromoterPayoutsSerializer(CamelCaseSerializer):
    class Meta:
        model = PromoterPayout
        fields = ["id", "created", "amount"]


class MinWithdrawalBalanceSerializer(PromoterSerializer):
    class Meta(PromoterSerializer.Meta):
        fields = ['min_withdrawal_balance']
