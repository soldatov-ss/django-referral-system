import logging

from django.contrib.auth.models import User

from referrals.config import config
from referrals.models import Promoter
from referrals.repositories.promoter_repository import promoter_repository
from referrals.services.referral_service import referral_service

logger = logging.getLogger(__name__)


class PromoterService:
    """
    Service class for managing Promoter-related operations.
    """

    def create_new_promoter(self, user: User) -> Promoter:
        referral_token = referral_service.generate_referral_token(user_id=user.id)
        referral_link = referral_service.generate_referral_link(base_referral_link=config.BASE_REFERRAL_LINK,
                                                                referral_token=referral_token)

        promoter = Promoter(
            user=user,
            referral_token=referral_token,
            referral_link=referral_link,
        )
        promoter.save()
        logger.info(f"Created new promoter {user.email}")

        return promoter

    def get_or_create_promoter(self, user: User) -> Promoter:
        promoter = promoter_repository.get_by_user_id(user.id)
        if not promoter:
            promoter = self.create_new_promoter(user=user)

        return promoter


promoter_service = PromoterService()
