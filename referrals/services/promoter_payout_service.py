import logging
import math
from decimal import Decimal
from typing import Optional

import pandas as pd
from pydantic import BaseModel

from referrals.helpers import parse_df_to_csv_string_without_index_col
from referrals.models import Promoter, PromoterPayout, PromoterCommission, Referral
from referrals.repositories import promoter_repository, promoter_payout_repository, promoter_commission_repository, \
    referral_repository

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
    def send_wise_csv_for_promoters_payouts(self, **kwargs):
        promoters = promoter_repository.get_wise_payout_promoters()

        data = []
        for promoter in promoters:
            if promoter.current_balance > 0 and promoter.current_balance >= promoter.min_withdrawal_balance:
                payout_data_row = PromoterPayoutDataRow(
                    name=promoter.user.get_full_name(),
                    recipientEmail=promoter.active_payout_method.payment_address,
                    amount=promoter.current_balance,
                    **kwargs,
                )

                data.append(payout_data_row.model_dump())
                promoter_payout_repository.create_payout(
                    promoter, promoter.current_balance, payout_method='wise'
                )
                promoter_commission_repository.mark_commission_paid(promoter)
        if data:
            df = pd.DataFrame(data)
            return parse_df_to_csv_string_without_index_col(df)

    def calculate_commission(self, user_id: int,
                             amount_paid: int,
                             invoice_external_id: Optional[int] = None) -> Optional[PromoterCommission]:
        referral = referral_repository.get_referral_by_user_id(user_id)
        if not referral:
            return

        has_received_commission = promoter_repository.check_promoter_get_commission_from_referral(
            referral.promoter, referral
        )
        if has_received_commission:
            logger.info(f"Referrer {referral.promoter_id} already received commission from referral {referral.id}")
            return

        commission = self.create_commission(referral, amount_paid, invoice_external_id)
        if commission:
            logger.info(
                f"Commission {commission.id} created for promoter {referral.promoter_id} from referral {referral.id}"
            )
        return commission

    def create_commission(self, referral: Referral,
                          amount_paid: int,
                          invoice_external_id: Optional[int] = None) -> Optional[PromoterCommission]:
        commission_amount = self.calculate_commission_amount(amount_paid, referral.commission_rate)

        commission = PromoterCommission(
            promoter=referral.promoter,
            referral=referral,
            amount=commission_amount,
            invoice_external_id=invoice_external_id,
        )
        commission.save()
        return commission

    @staticmethod
    def calculate_commission_amount(amount_paid: int, referral_commission_rate: Decimal) -> float:
        commission_rate = referral_commission_rate / 100
        price = amount_paid / 100

        return math.floor(Decimal(price) * commission_rate)

    @staticmethod
    def create_payout(promoter: Promoter, amount: float, payout_method):
        PromoterPayout.objects.create(
            promoter=promoter,
            amount=amount,
            payout_method=payout_method,
        )
        PromoterCommission.objects.filter(promoter=promoter, status="pending").update(status="paid")


promoter_payout_service = PromoterPayoutService()
