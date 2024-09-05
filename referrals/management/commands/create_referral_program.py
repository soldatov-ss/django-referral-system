from decimal import Decimal

from django.core.management.base import BaseCommand

from referrals.models import ReferralProgram


class Command(BaseCommand):
    help = "Create a new referral program with a specified commission rate and minimum withdrawal balance"

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Name of the referral program',
        )
        parser.add_argument(
            '--commission-rate',
            type=Decimal,
            required=True,
            help='Commission rate as a percentage (e.g., 5.00 for 5%)',
        )
        parser.add_argument(
            '--min-withdrawal-balance',
            type=Decimal,
            default=Decimal('0.00'),
            help='Minimum withdrawal balance for the referral program (default: 0.00)',
        )

    def handle(self, *args, **options):
        name = options['name']
        commission_rate = options['commission_rate']
        min_withdrawal_balance = options['min_withdrawal_balance']

        if commission_rate <= Decimal('0.00'):
            self.stderr.write(self.style.ERROR('Commission rate must be greater than 0.00'))
            return

        referral_program = ReferralProgram(
            name=name,
            commission_rate=commission_rate,
            min_withdrawal_balance=min_withdrawal_balance
        )

        referral_program.save()

        self.stdout.write(self.style.SUCCESS(
            f'Referral program "{name}" created successfully with a commission rate of {commission_rate}% and a minimum withdrawal balance of {min_withdrawal_balance}.'
        ))
