from typing import Optional

from .base_repository import BaseRepository
from referrals.models import Referral


class ReferralRepository(BaseRepository):

    def get_referrals_by_user_id(self, user_id: int) -> Optional[Referral]:
        return self.select_related("promoter__user").filter(promoter__user_id=user_id).all().order_by("-created")

    def get_referral_by_user_id_custom_relations(self, user_id: int, relation: str) -> Optional[Referral]:
        return self.select_related("promoter").filter(user_id=user_id).prefetch_related(f"user__{relation}").first()


referral_repository = ReferralRepository(model=Referral)
