import logging

from referrals.choices import PromoterCommissionStatusChoices
from referrals.models import Promoter, Referral, PromoterCommission
from referrals.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PromoterCommissionRepository(BaseRepository):

    def mark_commission_paid(self, promoter: Promoter):
        self.filter(
            promoter=promoter,
            status__in=[PromoterCommissionStatusChoices.PENDING.value, PromoterCommissionStatusChoices.FAILED.value],
        ).update(status=PromoterCommissionStatusChoices.PAID.value)

    def mark_commission_failed_with_reason(self, promoter: Promoter, failure_reason: str):
        self.filter(promoter=promoter, status=PromoterCommissionStatusChoices.PENDING.value).update(
            status=PromoterCommissionStatusChoices.FAILED.value, failure_reason=failure_reason
        )

    def get_referral_positive_commission(self, referral: Referral):
        query = self.filter(
            referral=referral,
            status__in=[PromoterCommissionStatusChoices.PENDING, PromoterCommissionStatusChoices.PAID]
        )
        return query.first()


promoter_commission_repository = PromoterCommissionRepository(model=PromoterCommission)
