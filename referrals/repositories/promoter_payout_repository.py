import logging
from typing import Optional

from referrals.models import Promoter, PromoterPayout

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PromoterPayoutRepository(BaseRepository):
    def create_payout(self, promoter: Promoter, amount: float, payout_method, tx_signature: Optional[str] = None):
        self.create(
            promoter=promoter,
            amount=amount,
            payout_method=payout_method,
            tx_signature=tx_signature,
        )


promoter_payout_repository = PromoterPayoutRepository(model=PromoterPayout)
