import logging

from .base_repository import BaseRepository
from referrals.models import Promoter, PromoterPayout

logger = logging.getLogger(__name__)


class PromoterPayoutRepository(BaseRepository):
    def create_payout(self, promoter: Promoter, amount: float, payout_method, tx_signature: str = None):
        self.create(
            promoter=promoter,
            amount=amount,
            payout_method=payout_method,
            tx_signature=tx_signature,
        )


promoter_payout_repository = PromoterPayoutRepository(model=PromoterPayout)
