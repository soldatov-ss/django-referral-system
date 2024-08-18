import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import get_template

from referrals.choices import ReferralStateChoices
from referrals.models import PromoterCommission, Promoter
from referrals.serializers import PromoterCommissionSerializer
# from ..services.promoter_payout_service import promoter_payout_service
from referrals.utils import append_query_params

logger = logging.getLogger(__name__)


class ReferralService:
    @staticmethod
    def send_referral_invitation_email(base_email: str, emails_to: list[str], invitation_link: str,
                                       promoter_full_name: str):
        """
        Sends an HTML email with an invitation link to the specified email address.
        """
        # TODO: configure subject, from email
        subject = "{} has invited you to join Cryptonary".format(promoter_full_name)
        invitation_link = append_query_params(invitation_link, {"ref-source": "email"})
        html_template_context = {
            "link": invitation_link,
            "promoter_full_name": promoter_full_name,
        }
        html_template = "referral_email_template.html"
        email_message = get_template(html_template).render(html_template_context)

        email = EmailMessage(
            subject,
            body=email_message,
            # from_email=api_settings.MAGIC_LINKS_EMAIL_FROM_ADDRESS,
            from_email=base_email,
            to=emails_to,
        )
        email.content_subtype = "html"
        email.send()

    @staticmethod
    def get_user_earnings(user: User):
        seven_days_ago = datetime.today().date() - timedelta(days=6)
        earnings = PromoterCommission.objects.filter(promoter__user=user, created__gte=seven_days_ago)
        serializer = PromoterCommissionSerializer(earnings, many=True)
        return serializer.data

    @staticmethod
    def aggregate_earnings_by_day(earnings):
        earnings_by_day = defaultdict(int)

        for earning in earnings:
            created_at = datetime.strptime(earning["created"], "%Y-%m-%dT%H:%M:%S.%fZ")
            day_of_week = created_at.strftime("%a")
            earnings_by_day[day_of_week] += earning["amount"]
        return earnings_by_day

    @staticmethod
    def get_last_7_days_earnings(earnings):
        today = datetime.today()
        last_7_days = [(today - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
        earnings_by_day = ReferralService.aggregate_earnings_by_day(earnings)
        statistics = [{"day": day[:2], "value": earnings_by_day.get(day, 0)} for day in last_7_days]
        return statistics

    @staticmethod
    def generate_referral_token(user_id: int) -> str:
        """
        Generate a unique referral code using the user's ID and the current timestamp,
        hashed for consistency in length and to obscure the user ID.

        :param user_id: The ID of the user from whom the referral code is being generated.
        :return: A unique referral code.
        """

        raw_code = f"{user_id}"
        hash_object = hashlib.sha256(raw_code.encode())
        referral_code = hash_object.hexdigest()[:10]

        return referral_code.upper()

    @staticmethod
    def generate_referral_link(base_referral_link: str, referral_token: str) -> str:
        """
        Generate a unique referral link with a referral token.
        """
        # TODO: APPSFLYER_BASE_LINK was as param
        return append_query_params(base_referral_link, {"ref": referral_token})

    @staticmethod
    def get_referrer_by_user_id(user_id: int) -> Optional[Promoter]:
        """
        Retrieve the promoter (referrer) associated with a given user ID.
        """
        try:
            user = User.objects.select_related("referral__promoter__user").filter(pk=user_id).first()
            return user.referral.promoter
        except User.DoesNotExist:
            return None
        except ObjectDoesNotExist:
            logger.error("User does not have referral relation")
            return None

    @staticmethod
    def handle_purchase_subscription(user: User, invoice: dict):
        """
        Handles the process of updating a referral subscription status to 'Active'
        when a subscription is created for a referred user.
        """
        try:
            user = User.objects.select_related("referral__promoter__user").filter(pk=user.id).first()
            promoter = user.referral.promoter
            if user.referral.status == ReferralStateChoices.SIGNUP:
                user.referral.status = ReferralStateChoices.ACTIVE
                user.referral.save()
                logger.info(f"User {user.email} became an active referral of {promoter.user.email}")
                # TODO: finish implementing
                # promoter_payout_service.calculate_commission(user.id, invoice)
        except ObjectDoesNotExist:
            logger.error(f"User with ID {user.id} has no referral associated.")

    @staticmethod
    @transaction.atomic
    def handle_user_refund(user: User, amount_refunded: int, invoice: dict):
        """
        Handles the process of refunding a referred user's subscription.
        """
        try:
            user = User.objects.select_related("referral__promoter__user").filter(pk=user.id).first()

            if user.referral.status == ReferralStateChoices.ACTIVE:
                user.referral.status = ReferralStateChoices.REFUND
                user.referral.save()
                # TODO: finish implementing
                # promoter_payout_service.calculate_refund(user.referral, amount_refunded, invoice)
                logger.info(f"User {user.email} has been refunded {amount_refunded}.")

        except ObjectDoesNotExist:
            logger.error(f"User with ID {user.id} has no referral associated.")


referral_service = ReferralService()
