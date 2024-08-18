# import logging
# import math
# from decimal import Decimal
# from email.mime.application import MIMEApplication
# from typing import Optional
#
# import pandas as pd
# from django.conf import settings
# from django.core.mail import EmailMessage
# from pydantic import BaseModel
# from solana.publickey import PublicKey
#
# from cryptonary_back.apps.integrations.solana.enums import (
#     SplTokensMintAddressEnum,
#     TransactionTypeEnum,
# )
# from cryptonary_back.apps.integrations.solana.solana_client import solana_client
# from cryptonary_back.apps.magic_link.settings import api_settings
# from cryptonary_back.apps.referrals.choices import PayoutMethodChoices, PromoterCommissionStatusChoices
# from cryptonary_back.apps.referrals.dtos.promoters_dtos import (
#     PromoterCryptoPayoutDataRow,
# )
# from cryptonary_back.apps.referrals.enums import CryptoPayoutTokenIdsEnum
# from cryptonary_back.apps.referrals.models import (
#     Promoter,
#     PromoterCommission,
#     PromoterPayout,
#     Referral,
# )
# from cryptonary_back.apps.referrals.repositories.promoter_commission_repository import (
#     promoter_commission_repository,
# )
# from cryptonary_back.apps.referrals.repositories.promoter_payout_repository import (
#     promoter_payout_repository,
# )
# from cryptonary_back.apps.referrals.repositories.promoter_repository import (
#     promoter_repository,
# )
# from cryptonary_back.apps.referrals.repositories.referral_repository import (
#     referral_repository,
# )
# from cryptonary_back.apps.solana_pay.services.solanapay_payment_service import (
#     solana_pay_payment_service,
# )
# from cryptonary_back.apps.subscriptions.repositories.invoice_repository import invoice_repository
# from cryptonary_back.scripts.helpers.file_parse_helpers import (
#     parse_df_to_csv_string_without_index_col,
# )
# from cryptonary_back.settings import WISE_PAYOUT_RECIPIENTS
# from ..exceptions import ViewException
#
# logger = logging.getLogger(__name__)
#
#
# class PromoterPayoutDataRow(BaseModel):
#     name: str
#     recipientEmail: str
#     amount: float
#     sourceCurrency: str = "USD"
#     targetCurrency: str = "USD"
#     amountCurrency: str = "target"
#     type: str = "EMAIL"
#
#
# class PromoterPayoutService:
#     def __init__.py(self):
#         self.CRYPTO_TOKEN_DECIMAL_PLACES = 6
#
#     # def make_crypto_payout_for_promoters(self):
#     #     promoters = promoter_repository.get_crypto_payout_promoters()
#     #
#     #     for promoter in promoters:
#     #         if promoter.current_balance > 0 and promoter.current_balance >= promoter.min_withdrawal_balance:
#     #             try:
#     #                 solana_recipient = PublicKey(promoter.active_payout_method.payment_address)
#     #             except ValueError:
#     #                 logger.error(
#     #                     f"Invalid Solana recipient address: {promoter.active_payout_method.payment_address} for promoter with id: {promoter.id}"
#     #                 )
#     #                 promoter_commission_repository.mark_commission_failed_with_reason(
#     #                     promoter,
#     #                     failure_reason=f"Invalid Solana recipient address: {promoter.active_payout_method.payment_address},"
#     #                     f" for promoter with id: {promoter.id}",
#     #                 )
#     #                 continue
#     #
#     #             token_price = solana_pay_payment_service.get_crypto_price_by_token_id(
#     #                 CryptoPayoutTokenIdsEnum.USDC.value
#     #             )
#     #             amount_in_crypto = promoter.current_balance / token_price
#     #             transaction_response = solana_client.send_transaction(
#     #                 recipient=solana_recipient, amount=amount_in_crypto, transaction_type=TransactionTypeEnum.SPL
#     #             )
#     #             if not transaction_response or not transaction_response.confirmation_status:
#     #                 promoter_commission_repository.mark_commission_failed_with_reason(
#     #                     promoter,
#     #                     failure_reason=f"Transaction failed: {transaction_response.tx_signature} for promoter with id: {promoter.id}",
#     #                 )
#     #                 continue
#     #
#     #             promoter_payout_repository.create_payout(
#     #                 promoter,
#     #                 promoter.current_balance,
#     #                 payout_method=PayoutMethodChoices.CRYPTO.value,
#     #                 tx_signature=transaction_response.tx_signature,
#     #             )
#     #             promoter_commission_repository.mark_commission_paid(promoter)
#
#     def send_wise_csv_for_promoters_payouts(self):
#         promoters = promoter_repository.get_wise_payout_promoters()
#
#         data = []
#         for promoter in promoters:
#             if promoter.current_balance > 0 and promoter.current_balance >= promoter.min_withdrawal_balance:
#                 payout_data_row = PromoterPayoutDataRow(
#                     name=promoter.user.get_full_name(),
#                     recipientEmail=promoter.active_payout_method.payment_address,
#                     amount=promoter.current_balance,
#                 )
#
#                 data.append(payout_data_row.model_dump())
#                 promoter_payout_repository.create_payout(
#                     promoter, promoter.current_balance, payout_method=PayoutMethodChoices.WISE.value
#                 )
#                 promoter_commission_repository.mark_commission_paid(promoter)
#         if data:
#             df = pd.DataFrame(data)
#             csv_string = parse_df_to_csv_string_without_index_col(df)
#
#             email = EmailMessage(
#                 subject="Referral Program Wise Payouts",
#                 body="csv file for payments",
#                 from_email=api_settings.MAGIC_LINKS_EMAIL_FROM_ADDRESS,
#                 to=WISE_PAYOUT_RECIPIENTS,
#             )
#             csv_attachment = MIMEApplication(csv_string, Name="promoters.csv")
#             email.attach(csv_attachment)
#             email.send(fail_silently=False)
#             logger.info("Email with promoters.csv successfully sent")

    # def calculate_commission(self, user_id: int, invoice: dict) -> Optional[PromoterCommission]:
    #     referral = referral_repository.get_referral_by_user_id_custom_relations(user_id, "chargebee_subscriptions")
    #     if not referral:
    #         return
    #
    #     has_received_commission = promoter_repository.check_promoter_get_commission_from_referral(
    #         referral.promoter, referral
    #     )
    #     if has_received_commission:
    #         logger.info(f"Referrer {referral.promoter.id} already received commission from referral {referral.id}")
    #         return
    #
    #     commission = self.create_commission(referral, invoice)
    #     if commission:
    #         logger.info(
    #             f"Commission {commission.id} created for promoter {referral.promoter.id} from referral {referral.id}"
    #         )
    #     return commission
    #
    # def create_commission(self, referral: Referral, invoice: dict) -> Optional[PromoterCommission]:
    #     if not invoice:
    #         logger.warning(f"No paid invoice was provided for user {referral.user.id}")
    #         return None
    #
    #     commission_amount = self.calculate_commission_amount(invoice["amount_paid"], referral.commission_rate)
    #
    #     commission = PromoterCommission(
    #         promoter=referral.promoter,
    #         referral=referral,
    #         amount=commission_amount,
    #         invoice_external_id=invoice["id"],
    #     )
    #     commission.save()
    #     return commission

#     @staticmethod
#     def calculate_commission_amount(invoice_amount_paid: int, referral_commission_rate: Decimal) -> float:
#         commission_rate = referral_commission_rate / 100
#         price = invoice_amount_paid / 100
#
#         return math.floor(Decimal(price) * commission_rate)
#
#     @staticmethod
#     def create_payout(promoter: Promoter, amount: float, payout_method):
#         PromoterPayout.objects.create(
#             promoter=promoter,
#             amount=amount,
#             payout_method=payout_method,
#         )
#         PromoterCommission.objects.filter(promoter=promoter, status="pending").update(status="paid")
#
#     def check_sender_address_crypto_balance_and_send_csv_report(self):
#         crypto_promoters = promoter_repository.get_crypto_payout_promoters()
#         usdc_token_price = solana_pay_payment_service.get_crypto_price_by_token_id(CryptoPayoutTokenIdsEnum.USDC.value)
#         data = []
#         total_amount = 0
#
#         # Send warning email SOLANA_SENDER_KEYPAIR is not specified
#         if not settings.SOLANA_SENDER_KEYPAIR:
#             email_subject = "[IMPORTANT] Sender key pair for the crypto payout is missing"
#             email = EmailMessage(
#                 subject=email_subject,
#                 body="It is necessary to add a secret key to the environment variables to pay commission to promoters",
#                 from_email=api_settings.MAGIC_LINKS_EMAIL_FROM_ADDRESS,
#                 to=WISE_PAYOUT_RECIPIENTS,
#             )
#             email.send(fail_silently=False)
#             logger.info("Warning email about crypto payout was sent")
#
#         for promoter in crypto_promoters:
#             current_promoter_balance = promoter.current_balance
#             if current_promoter_balance > 0 and current_promoter_balance >= promoter.min_withdrawal_balance:
#                 total_amount += current_promoter_balance
#                 crypto_payout_data_row = PromoterCryptoPayoutDataRow(
#                     name=promoter.user.get_full_name(),
#                     email=promoter.user.email,
#                     amount=current_promoter_balance / usdc_token_price,
#                     address=promoter.active_payout_method.payment_address,
#                 )
#                 data.append(crypto_payout_data_row.model_dump())
#
#         total_promoters_usdc_balance = round(total_amount / usdc_token_price, self.CRYPTO_TOKEN_DECIMAL_PLACES)
#
#         if data:
#             usdc_sender_balance = solana_client.get_spl_token_balance_by_address(
#                 PublicKey(settings.SOLANA_SENDER_ADDRESS), SplTokensMintAddressEnum.USDC
#             )
#
#             df = pd.DataFrame(data)
#             csv_string = parse_df_to_csv_string_without_index_col(df)
#             email_subject = (
#                 "Referral Program: Report before crypto payout"
#                 if usdc_sender_balance >= total_promoters_usdc_balance
#                 else "[IMPORTANT!] Sender wallet does not have a sufficient balance to make crypto payout"
#             )
#
#             email = EmailMessage(
#                 subject=email_subject,
#                 body=f"Report in CSV format before automatic crypto payment to promoters.\n\n"
#                 f"Crypto payments will be sent 12 hours after receiving this email.\n\n"
#                 f"Total amount to pay: {total_promoters_usdc_balance} USDC\n"
#                 f"Total balance on the sender crypto wallet: {usdc_sender_balance} USDC\n",
#                 from_email=api_settings.MAGIC_LINKS_EMAIL_FROM_ADDRESS,
#                 to=WISE_PAYOUT_RECIPIENTS,
#             )
#             csv_attachment = MIMEApplication(csv_string, Name="crypto-payout.csv")
#             email.attach(csv_attachment)
#             email.send(fail_silently=False)
#             logger.info("Email with crypto-payout.csv successfully sent")
#
#     @staticmethod
#     def calculate_refund(referral: Referral, amount_refunded: int, invoice: dict):
#         db_invoice = invoice_repository.get_invoice_by_id_or_404(invoice["id"])
#         db_invoice.refunded_amount += amount_refunded
#         db_invoice.save()
#
#         referral_commission = promoter_commission_repository.get_referral_positive_commission(referral, invoice["id"])
#         if not referral_commission:
#             logger.error(f"No commission found for referral with id {referral.id} and invoice with id {invoice['id']}.")
#             raise ViewException(
#                 f"No commission found for referral with id {referral.id} and invoice with id {invoice['id']}.",
#                 status_code=404
#             )
#
#         commission_paid = referral_commission.amount
#         commission_refund_amount = -math.floor(commission_paid * amount_refunded / db_invoice.amount_paid)
#
#         commission = PromoterCommission(
#             promoter=referral.promoter,
#             referral=referral,
#             amount=commission_refund_amount,
#             status=PromoterCommissionStatusChoices.REFUND,
#             invoice_external_id=db_invoice.id,
#         )
#         commission.save()
#         return commission
#
#
# promoter_payout_service = PromoterPayoutService()
