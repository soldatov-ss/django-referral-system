from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.functional import cached_property

from referrals.choices import InvitationMethodChoices, ReferralStateChoices, \
    PromoterCommissionStatusChoices


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super().save(*args, **kwargs)


class ReferralProgram(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Commission rate as a percentage",
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    is_active = models.BooleanField(
        default=True, help_text="Indicates if this is the currently active referral program"
    )
    min_withdrawal_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Minimum balance required to withdraw earnings"
    )

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.is_active:
            ReferralProgram.objects.filter(is_active=True).update(is_active=False)
            Promoter.objects.filter(min_withdrawal_balance__lt=self.min_withdrawal_balance).update(
                min_withdrawal_balance=self.min_withdrawal_balance
            )

        super(ReferralProgram, self).save(*args, **kwargs)

    @classmethod
    def get_active_referral_program(cls):
        return cls.objects.filter(is_active=True).first()


class PayoutMethod(models.Model):
    method = models.CharField(max_length=20, help_text="Payout method (e.g., wise, crypto, etc.)")
    payment_address = models.CharField(max_length=100, help_text="Payment address (email or solana wallet)")

    def __str__(self):
        return self.method


class Promoter(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="promoter")
    referral_token = models.CharField(max_length=256, blank=True, null=True, unique=True, help_text="Referral token")
    referral_link = models.CharField(max_length=256, blank=True, null=True, unique=True, help_text="Referral link")
    active_payout_method = models.ForeignKey(PayoutMethod, on_delete=models.SET_NULL, null=True, blank=True)
    link_clicked = models.IntegerField(default=0)
    min_withdrawal_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Custom minimum balance required to withdraw earnings",
    )

    @cached_property
    def total_earned(self) -> int:
        return self.promoter_commission.aggregate(total=Sum("amount"))["total"] or 0

    @cached_property
    def total_paid(self) -> int:
        return (
                self.promoter_payouts.aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
        )

    @cached_property
    def current_balance(self) -> int:
        return self.total_earned - self.total_paid

    def __str__(self):
        return f"{self.user.email} - {self.referral_link}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            active_program = ReferralProgram.get_active_referral_program()
            if active_program:
                self.min_withdrawal_balance = active_program.min_withdrawal_balance
        super(Promoter, self).save(*args, **kwargs)


class Referral(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral")
    promoter = models.ForeignKey(Promoter, related_name="referrals", on_delete=models.CASCADE)
    invitation_method = models.CharField(max_length=10, choices=InvitationMethodChoices.choices)
    status = models.CharField(max_length=10, choices=ReferralStateChoices.choices)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Commission rate at the moment of creating the referral", default=0.00
    )

    def save(self, *args, **kwargs):
        if self.pk is None:
            active_program = ReferralProgram.get_active_referral_program()
            if active_program:
                self.commission_rate = active_program.commission_rate
        super().save(*args, **kwargs)


class PromoterCommission(TimeStampedModel):
    promoter = models.ForeignKey(Promoter, related_name="promoter_commission", on_delete=models.CASCADE)
    referral = models.ForeignKey(Referral, related_name="referral_commission", on_delete=models.CASCADE)
    amount = models.IntegerField(null=True)
    status = models.CharField(
        max_length=10, choices=PromoterCommissionStatusChoices.choices, default=PromoterCommissionStatusChoices.PENDING
    )
    failure_reason = models.TextField(null=True, blank=True)
    invoice_external_id = models.CharField(null=True, max_length=255, blank=True, help_text="e.g. Chargebee invoice ID")


class PromoterPayout(TimeStampedModel):
    promoter = models.ForeignKey(Promoter, related_name="promoter_payouts", on_delete=models.CASCADE)
    amount = models.IntegerField()
    payout_method = models.CharField(max_length=20, null=False, help_text="Payout method (e.g., wise, crypto, etc.)")
    tx_signature = models.CharField(max_length=255, null=True, blank=True)
