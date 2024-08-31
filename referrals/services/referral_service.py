import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template

from referrals.choices import ReferralStateChoices
from referrals.config import config
from referrals.models import PromoterCommission, Promoter
from referrals.serializers import PromoterCommissionSerializer
from referrals.services.promoter_payout_service import promoter_payout_service
from referrals.utils import append_query_params

logger = logging.getLogger(__name__)


class ReferralService:
    """
    Service class that handles operations related to referral programs, including sending invitation emails,
    managing user earnings, generating referral tokens and links, and handling subscriptions and refunds.
    """

    @staticmethod
    def send_referral_invitation_email(emails_to: list[str], invitation_link: str,
                                       promoter_full_name: str, subject: str, template_path: str,
                                       from_email: str = config.BASE_EMAIL) -> bool:
        """
        Sends an HTML email with an invitation link to the specified email addresses.

        :param emails_to: List of email addresses to send the invitation to.
        :param invitation_link: The referral invitation link.
        :param promoter_full_name: Full name of the promoter.
        :param subject: Subject of the email.
        :param template_path: Path to the HTML template for the email.
        :param from_email: The email address that will appear in the 'from' field.

        :return: True if the email was sent successfully, False otherwise.
        """
        invitation_link = append_query_params(invitation_link, {"ref-source": "email"})
        html_template_context = {
            "link": invitation_link,
            "promoter_full_name": promoter_full_name,
        }

        try:
            template = get_template(template_path)
            email_message = template.render(html_template_context)

            email = EmailMessage(
                subject,
                body=email_message,
                from_email=from_email,
                to=emails_to,
            )
            email.content_subtype = "html"
            email.send()
            logging.info(f"Referral invitation email sent to {emails_to}")
            return True
        except TemplateDoesNotExist:
            logging.error(f"Template '{template_path}' does not exist.")
            return False

    @staticmethod
    def get_user_earnings(user: User):
        """
        Retrieves the earnings of a user within the last 7 days.

        Filters the commissions associated with the user's promoter account that were created within
        the last 7 days, serializes the data, and returns it.

        Args:
            user (User): The user whose earnings are to be retrieved.

        Returns:
            list[dict]: A list of serialized commission data for the user's earnings.
        """
        seven_days_ago = datetime.today().date() - timedelta(days=6)
        earnings = PromoterCommission.objects.filter(promoter__user=user, created__gte=seven_days_ago)
        serializer = PromoterCommissionSerializer(earnings, many=True)
        return serializer.data

    @staticmethod
    def aggregate_earnings_by_day(earnings: list[dict]) -> dict[str, int]:
        """
        Aggregates earnings by the day of the week.

        Processes a list of earnings, grouping the total earnings by the day of the week they were created.

        Args:
            earnings (list[dict]): A list of earnings with their creation dates.

        Returns:
            dict[str, int]: A dictionary mapping each day of the week to the total earnings for that day.
        """
        earnings_by_day = defaultdict(int)

        for earning in earnings:
            created_at = datetime.strptime(earning["created"], "%Y-%m-%dT%H:%M:%S.%fZ")
            day_of_week = created_at.strftime("%a")
            earnings_by_day[day_of_week] += earning["amount"]
        return earnings_by_day

    @staticmethod
    def get_last_7_days_earnings(earnings: list[dict]) -> list[dict]:
        """
        Retrieves the earnings statistics for the last 7 days.

        Aggregates earnings data by the day of the week for the last 7 days, ensuring each day is represented
        even if there were no earnings on that day.

        Args:
            earnings (list[dict]): A list of earnings with their creation dates.

        Returns:
            list[dict]: A list of dictionaries, each containing the day (as a string) and the corresponding earnings value.
        """
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
    def handle_purchase_subscription(user: User,
                                     amount_paid: int,
                                     invoice_external_id: Optional[int] = None) -> Optional[PromoterCommission]:
        """
        Handles the process of updating a referral subscription status to 'Active'
        when a subscription is created for a referred user.

        Args:
            user (User): The user whose subscription is being handled.
            amount_paid (int): The amount paid for the subscription in cents.
            invoice_external_id (Optional[int]): An external ID for the invoice (optional).

        Returns:
            Optional[PromoterCommission]: The commission generated from the subscription, or None if no commission is generated.
        """
        try:
            user = User.objects.select_related("referral__promoter__user").filter(pk=user.id).first()
            promoter = user.referral.promoter
            if user.referral.status == ReferralStateChoices.SIGNUP:
                user.referral.status = ReferralStateChoices.ACTIVE
                user.referral.save()
                commission = promoter_payout_service.calculate_commission(user.id, amount_paid, invoice_external_id)
                logger.info(f"User {user.email} became an active referral of {promoter.user.email}")
                return commission
        except ObjectDoesNotExist:
            logger.error(f"User with ID {user.id} has no referral associated.")

    @staticmethod
    @transaction.atomic
    def handle_user_refund(user: User, amount_refunded: int, amount_paid: int,
                           invoice_external_id: Optional[int] = None) -> Optional[PromoterCommission]:
        """
        Handles the process of refunding a referred user's subscription.

        This method updates the user's referral status to 'Refund' and calculates the refund commission.

        Args:
            user (User): The user whose refund is being processed.
            amount_refunded (int): The amount refunded in cents.
            amount_paid (int): The original amount paid for the subscription in cents.
            invoice_external_id (Optional[int]): An external ID for the invoice (optional).

        Returns:
            Optional[PromoterCommission]: The refund commission generated from the refund, or None if no commission is generated.
        """
        try:
            user = User.objects.select_related("referral__promoter__user").filter(pk=user.id).first()

            if user.referral.status == ReferralStateChoices.ACTIVE:
                user.referral.status = ReferralStateChoices.REFUND
                user.referral.save()
                commission = promoter_payout_service.calculate_refund(user.referral, amount_refunded, amount_paid,
                                                                      invoice_external_id)
                logger.info(f"User {user.email} has been refunded {amount_refunded}.")
                return commission
        except ObjectDoesNotExist:
            logger.error(f"User with ID {user.id} has no referral associated.")


referral_service = ReferralService()
