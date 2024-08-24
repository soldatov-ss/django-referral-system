from django.db import models


class ReferralStateChoices(models.TextChoices):
    SIGNUP = "signup"
    ACTIVE = "active"
    REFUND = "refund"


class InvitationMethodChoices(models.TextChoices):
    EMAIL = "email"
    LINK = "link"


class PromoterCommissionStatusChoices(models.TextChoices):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUND = "refund"
