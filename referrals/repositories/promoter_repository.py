import logging
from typing import Optional

from referrals.models import Promoter, Referral
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PromoterRepository(BaseRepository):
    def get_by_user_id(self, user_id: int) -> Optional[Promoter]:
        return self.select_related("user").filter(user_id=user_id).first()

    def get_by_referral_token(self, referral_token: str) -> Optional[Promoter]:
        return self.select_related("user").filter(referral_token=referral_token).first()

    def get_wise_payout_promoters(self):
        return (
            self.select_related("user", "active_payout_method").filter(
                active_payout_method__method="wise")
        )

    def check_promoter_get_commission_from_referral(self, promoter: Promoter, referral: Referral) -> bool:
        return self.filter(promoter_commission__referral=referral, pk=promoter.id).exists()


promoter_repository = PromoterRepository(model=Promoter)
