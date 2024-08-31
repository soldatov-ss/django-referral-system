import logging
import math
from decimal import Decimal
from typing import Optional

import pandas as pd
from pydantic import BaseModel

from referrals.choices import PromoterCommissionStatusChoices
from referrals.exceptions import ViewException
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
    def send_wise_csv_for_promoters_payouts(self, **kwargs) -> Optional[str]:
        """
        Generates a CSV file for Wise payouts and processes payouts for eligible promoters.

        This method retrieves all promoters eligible for Wise payouts, generates the necessary
        payout data, and creates payouts for those promoters whose current balance meets or exceeds
        the minimum withdrawal balance. The resulting data is converted into a CSV format string.

        Args:
            **kwargs: Additional keyword arguments to pass to the `PromoterPayoutDataRow`.

        Returns:
            Optional[str]: A CSV formatted string containing payout data, or None if no data is available.
        """
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
        """
        Calculates and creates a commission for a promoter based on the referral's payment.

        This method checks if a commission has already been received for the given referral.
        If not, it calculates the commission amount and creates a new `PromoterCommission` entry.

        Args:
            user_id (int): The ID of the user who made the payment.
            amount_paid (int): The amount paid by the user in cents.
            invoice_external_id (Optional[int]): An optional external invoice ID.

        Returns:
            Optional[PromoterCommission]: The created commission, or None if no commission was created.
        """
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
        """
        Creates a new commission entry for a promoter based on a referral's payment.

        Args:
            referral (Referral): The referral for which the commission is being created.
            amount_paid (int): The amount paid by the user in cents.
            invoice_external_id (Optional[int]): An optional external invoice ID.

        Returns:
            Optional[PromoterCommission]: The created commission, or None if no commission was created.
        """
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
        """
        Calculates the commission amount based on the payment amount and referral commission rate.

        Args:
            amount_paid (int): The amount paid by the user in cents.
            referral_commission_rate (Decimal): The commission rate associated with the referral.

        Returns:
            float: The calculated commission amount.
        """
        commission_rate = referral_commission_rate / 100
        price = amount_paid / 100

        return math.floor(Decimal(price) * commission_rate)

    @staticmethod
    def create_payout(promoter: Promoter, amount: float, payout_method):
        """
        Creates a payout record for a promoter and marks their pending commissions as paid.

        Args:
            promoter (Promoter): The promoter receiving the payout.
            amount (float): The payout amount.
            payout_method (str): The method used for the payout (e.g., 'wise', 'crypto').

        Returns:
            None
        """
        PromoterPayout.objects.create(
            promoter=promoter,
            amount=amount,
            payout_method=payout_method,
        )
        PromoterCommission.objects.filter(promoter=promoter, status="pending").update(status="paid")

    @staticmethod
    def calculate_refund(referral: Referral, amount_refunded: int, amount_paid: int,
                         invoice_external_id: Optional[int] = None) -> PromoterCommission:
        """
        Calculates the refund amount for a promoter's commission and creates a refund record.

        Args:
            referral (Referral): The referral associated with the refund.
            amount_refunded (int): The amount refunded in cents.
            amount_paid (int): The original amount paid in cents.
            invoice_external_id (Optional[int]): An optional external invoice ID.

        Returns:
            PromoterCommission: The created refund commission entry.

        Raises:
            ViewException: If no positive commission is found for the referral.
        """
        referral_commission = promoter_commission_repository.get_referral_positive_commission(referral)
        if not referral_commission:
            raise ViewException(
                f"No commission found for referral with id {referral.id}.",
                status_code=404
            )

        commission_paid = referral_commission.amount
        commission_refund_amount = -math.floor(commission_paid * amount_refunded / amount_paid)

        commission = PromoterCommission(
            promoter=referral.promoter,
            referral=referral,
            amount=commission_refund_amount,
            status=PromoterCommissionStatusChoices.REFUND,
            invoice_external_id=invoice_external_id,
        )
        commission.save()
        return commission


promoter_payout_service = PromoterPayoutService()
