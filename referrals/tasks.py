# import logging
#
# from celery_once import QueueOnce
#
# from cryptonary_back.apps.referrals.services.promoter_payout_service import (
#     promoter_payout_service,
# )
# from cryptonary_back.apps.referrals.services.referral_service import referral_service
# from cryptonary_back.celery import app
# from cryptonary_back.celery_queues import CeleryRedisQueues
#
# referral_logger = logging.getLogger("referral_logger")
#
#
# @app.task(base=QueueOnce, once={"graceful": True}, queue=CeleryRedisQueues.USERS.value)
# def send_referral_invitation_email_task(emails_to: list[str], invitation_link: str, promoter_full_name: str):
#     referral_service.send_referral_invitation_email(emails_to, invitation_link, promoter_full_name)
#     referral_logger.info(f"Sending invitation emails to: {emails_to}")
#
#
# @app.task(base=QueueOnce, once={"graceful": True}, queue=CeleryRedisQueues.SCHEDULED.value)
# def send_crypto_payout_to_promoters():
#     referral_logger.info("Sending crypto payouts to promoters")
#     promoter_payout_service.make_crypto_payout_for_promoters()
#
#
# @app.task(base=QueueOnce, once={"graceful": True}, queue=CeleryRedisQueues.SCHEDULED.value)
# def send_wise_csv_for_promoters_payouts():
#     referral_logger.info("Sending wise CSV for promoters payouts")
#     promoter_payout_service.send_wise_csv_for_promoters_payouts()
#
#
# @app.task(base=QueueOnce, once={"graceful": True}, queue=CeleryRedisQueues.SCHEDULED.value)
# def send_crypto_csv_report_for_promoters_payouts():
#     referral_logger.info("Sending crypto report CSV for promoters payouts")
#     promoter_payout_service.check_sender_address_crypto_balance_and_send_csv_report()
