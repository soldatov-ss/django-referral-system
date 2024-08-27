import logging

import pandas as pd
from pydantic import BaseModel

from referrals.helpers import parse_df_to_csv_string_without_index_col
from referrals.models import Promoter, PromoterPayout, PromoterCommission
from referrals.repositories import promoter_repository, promoter_payout_repository, promoter_commission_repository

logger = logging.getLogger(__name__)


class PromoterPayoutDataRow(BaseModel):
    name: str
    recipientEmail: str
    amount: float
    sourceCurrency: str = "USD"
    targetCurrency: str = "USD"
    amountCurrency: str = "target"
    type: str = "EMAIL"


class PromoterPayoutService:
    def send_wise_csv_for_promoters_payouts(self):
        promoters = promoter_repository.get_wise_payout_promoters()

        data = []
        for promoter in promoters:
            if promoter.current_balance > 0 and promoter.current_balance >= promoter.min_withdrawal_balance:
                payout_data_row = PromoterPayoutDataRow(
                    name=promoter.user.get_full_name(),
                    recipientEmail=promoter.active_payout_method.payment_address,
                    amount=promoter.current_balance,
                )

                data.append(payout_data_row.model_dump())
                promoter_payout_repository.create_payout(
                    promoter, promoter.current_balance, payout_method='wise'
                )
                promoter_commission_repository.mark_commission_paid(promoter)
        if data:
            df = pd.DataFrame(data)
            return parse_df_to_csv_string_without_index_col(df)

    @staticmethod
    def create_payout(promoter: Promoter, amount: float, payout_method):
        PromoterPayout.objects.create(
            promoter=promoter,
            amount=amount,
            payout_method=payout_method,
        )
        PromoterCommission.objects.filter(promoter=promoter, status="pending").update(status="paid")


promoter_payout_service = PromoterPayoutService()
