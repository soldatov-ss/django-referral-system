import asyncio
import math
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction
from django.template.exceptions import TemplateDoesNotExist
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from referrals.choices import InvitationMethodChoices, PromoterCommissionStatusChoices, ReferralStateChoices
from referrals.config import config
from referrals.enums import CryptoPayoutTokenIdsEnum, PayoutStatusEnum, ReferralStateEnum
from referrals.exceptions import ViewException
from referrals.helpers import parse_df_to_csv_string_without_index_col
from referrals.models import PayoutMethod, Promoter, PromoterCommission, PromoterPayout, Referral, ReferralProgram
from referrals.repositories import promoter_commission_repository, promoter_payout_repository, promoter_repository
from referrals.repositories.base_repository import BaseRepository
from referrals.repositories.decorators import sync_to_async
from referrals.serializers import PromoterPayoutsSerializer, PromoterSerializer, ReferralSerializer
import sys

from referrals.services import promoter_service, referral_service
_referral_service_module = sys.modules['referrals.services.referral_service']
from referrals.services.promoter_payout_service import promoter_payout_service
from referrals.utils import append_query_params


class ReferralProgramViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(name='test_program', commission_rate=20.00,
                                                              is_active=True, min_withdrawal_balance=10)
        cls.user = User.objects.create_user(username='test-user', email='test@example.com', password='Password123')
        cls.user2 = User.objects.create_user(username='test-user2', email='test2@example.com', password='Password321')
        cls.user3 = User.objects.create_user(username='test-user3', email='test3@example.com', password='Password121')
        cls.user4 = User.objects.create_user(username='test-user4', email='test4@example.com', password='Password111')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='test-token')
        cls.referral = Referral.objects.create(
            user=cls.user2,
            promoter=cls.promoter,
            status=ReferralStateChoices.ACTIVE
        )
        cls.referral2 = Referral.objects.create(
            user=cls.user3,
            promoter=cls.promoter,
            status=ReferralStateChoices.ACTIVE
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.promoter.refresh_from_db()

    def test_create_referral_success(self):
        url = reverse('referrals-list')
        data = {
            "email": self.user4.email,
            "referral_token": "test-token",
            "referral_source": InvitationMethodChoices.EMAIL.value,
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Referral.objects.filter(user=self.user4).exists())

        referral = Referral.objects.get(user=self.user4)
        self.assertEqual(referral.promoter, self.promoter)
        self.assertEqual(referral.invitation_method, InvitationMethodChoices.EMAIL.value)
        self.assertEqual(referral.status, ReferralStateChoices.SIGNUP.value)

    def test_create_referral_self_referral(self):
        url = reverse('referrals-list')
        data = {
            "email": self.user.email,
            "referral_token": "test-token",
            "referral_source": InvitationMethodChoices.LINK.value,
        }

        with self.assertRaises(ViewException) as context:
            self.client.post(url, data, format='json')

        self.assertIn("You can't refer to yourself.", str(context.exception))

    def test_create_referral_invalid_token(self):
        url = reverse('referrals-list')
        data = {
            "email": self.user4.email,
            "referral_token": "invalid-token",  # Invalid token
            "referral_source": InvitationMethodChoices.LINK.value,
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Referral.objects.filter(user=self.user4).exists())

    def test_list_referrals(self):
        url = reverse('referrals-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

        expected_data = ReferralSerializer([self.referral, self.referral2], many=True).data

        response_data_sorted = sorted(response.data["results"], key=lambda x: x['userId'])
        expected_data_sorted = sorted(expected_data, key=lambda x: x['userId'])

        self.assertEqual(response_data_sorted, expected_data_sorted)

    def test_list_referrals_empty(self):
        Referral.objects.all().delete()

        url = reverse('referrals-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["results"], [])

    def test_get_referral_link(self):
        self.client.force_authenticate(user=self.user2)

        url = reverse('referrals-get-referral-link')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Promoter.objects.filter(user=self.user2).exists())

        self.assertIn('referralLink', response.data)
        self.assertEqual(response.data['referralLink'], self.user2.promoter.referral_link)

    def test_retrieve_promoter(self):
        url = reverse('referrals-retrieve-promoter')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        promoter = Promoter.objects.get(user=self.user)
        serializer = PromoterSerializer(promoter)

        self.assertEqual(response.data, serializer.data)

    def test_set_payout_method_to_promoter(self):
        url = reverse('referrals-set-payout-method')
        data = {
            "method": "wise",
            "payment_address": "test@example.com"
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.promoter.refresh_from_db()
        self.assertEqual(self.promoter.active_payout_method.method, "wise")
        self.assertEqual(self.promoter.active_payout_method.payment_address, "test@example.com")

    def test_set_min_withdrawal_balance_success(self):
        url = reverse('referrals-set-min-withdrawal-balance')
        data = {
            "min_withdrawal_balance": 15.00
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.promoter.refresh_from_db()
        self.assertEqual(self.promoter.min_withdrawal_balance, 15.00)

        expected_data = PromoterSerializer(self.promoter).data
        self.assertEqual(response.data, expected_data)

    def test_set_min_withdrawal_balance_below_program_min(self):
        url = reverse('referrals-set-min-withdrawal-balance')
        data = {
            "min_withdrawal_balance": 5.00
        }

        with self.assertRaises(ViewException) as context:
            self.client.patch(url, data, format='json')

        self.assertIn(
            "Min withdrawal balance must be greater than or equal to the referral program's min withdrawal balance",
            str(context.exception))

    def test_increment_link_clicked_success(self):
        url = reverse('referrals-increment-link-clicked')
        data = {
            "referral_token": "test-token"
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Link clicked count incremented successfully")

        self.promoter.refresh_from_db()
        self.assertEqual(self.promoter.link_clicked, 1)

    def test_increment_link_clicked_invalid_token(self):
        url = reverse('referrals-increment-link-clicked')
        data = {
            "referral_token": "invalid-token"
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_promoter_payment_history_with_payouts(self):
        payout1 = PromoterPayout.objects.create(
            promoter=self.promoter, amount=100, payout_method="wise", tx_signature="tx123"
        )
        payout2 = PromoterPayout.objects.create(
            promoter=self.promoter, amount=200, payout_method="crypto", tx_signature="tx456"
        )

        url = reverse('referrals-promoter-payment-history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        expected_data = PromoterPayoutsSerializer([payout2, payout1], many=True).data
        self.assertEqual(response.data, expected_data)

    def test_promoter_payment_history_no_payouts(self):
        url = reverse('referrals-promoter-payment-history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_promoter_recent_earnings(self):
        seven_days_ago = timezone.now() - timedelta(days=6)
        PromoterCommission.objects.create(promoter=self.promoter, amount=100, referral=self.referral,
                                          created=seven_days_ago)
        PromoterCommission.objects.create(promoter=self.promoter, amount=200, referral=self.referral2,
                                          created=timezone.now())

        url = reverse('referrals-promoter-recent-earnings')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 7)

        total_earnings = sum(item['value'] for item in response.data)
        self.assertEqual(total_earnings, 300)

    def test_promoter_recent_earnings_no_data(self):
        url = reverse('referrals-promoter-recent-earnings')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 7)

        # Check that all values are 0 when there's no data
        for day_data in response.data:
            self.assertEqual(day_data['value'], 0)

    def test_promoter_payment_history(self):
        payout1 = PromoterPayout.objects.create(
            promoter=self.promoter, amount=100, payout_method="wise", tx_signature="tx123"
        )
        payout2 = PromoterPayout.objects.create(
            promoter=self.promoter, amount=200, payout_method="crypto", tx_signature="tx456"
        )

        url = reverse('referrals-promoter-payment-history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

        self.assertEqual(response.data[0]['amount'], 200)
        self.assertEqual(response.data[1]['amount'], 100)

    def test_promoter_payment_history_no_data(self):
        url = reverse('referrals-promoter-payment-history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 0)


class ReferralServiceTestCase(TestCase):
    commission_rate = 20.00

    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(name='test_program',
                                                              commission_rate=cls.commission_rate,
                                                              is_active=True, min_withdrawal_balance=10)
        cls.user = User.objects.create_user(username='test-user', email='test@example.com', password='Password123')
        cls.user2 = User.objects.create_user(username='test-user2', email='test2@example.com', password='Password321')
        cls.user3 = User.objects.create_user(username='test-user3', email='test3@example.com', password='Password121')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='test-token')
        cls.referral = Referral.objects.create(
            user=cls.user2,
            promoter=cls.promoter,
            status=ReferralStateChoices.SIGNUP
        )
        cls.referral2 = Referral.objects.create(
            user=cls.user3,
            promoter=cls.promoter,
            status=ReferralStateChoices.SIGNUP
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.referral.refresh_from_db()
        self.referral2.refresh_from_db()

    def test_get_user_earnings(self):
        seven_days_ago = timezone.now() - timedelta(days=6)
        PromoterCommission.objects.create(promoter=self.promoter, referral=self.referral, amount=100,
                                          created=seven_days_ago)
        PromoterCommission.objects.create(promoter=self.promoter, referral=self.referral2, amount=200,
                                          created=timezone.now())

        earnings = referral_service.get_user_earnings(self.user)
        self.assertEqual(len(earnings), 2)
        self.assertEqual(earnings[0]['amount'], 100)
        self.assertEqual(earnings[1]['amount'], 200)

    def test_aggregate_earnings_by_day(self):
        earnings = [
            {"created": datetime.today().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "amount": 100},
            {"created": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "amount": 200},
        ]
        aggregated_earnings = referral_service.aggregate_earnings_by_day(earnings)
        today = datetime.today().strftime("%a")
        yesterday = (datetime.today() - timedelta(days=1)).strftime("%a")

        self.assertEqual(aggregated_earnings[today], 100)
        self.assertEqual(aggregated_earnings[yesterday], 200)

    def test_generate_referral_token(self):
        referral_token = referral_service.generate_referral_token(self.user.id)
        self.assertEqual(len(referral_token), 10)

    def test_get_referrer_by_user_id(self):
        referrer = referral_service.get_referrer_by_user_id(self.user2.id)
        self.assertEqual(referrer, self.promoter)

    def test_get_referrer_by_user_id_unknown_user(self):
        referrer = referral_service.get_referrer_by_user_id(999999)
        self.assertIsNone(referrer)

    def test_handle_purchase_subscription(self):
        self.referral.status = ReferralStateChoices.SIGNUP
        self.referral.save()

        amount_paid = 15000  # amount in cents

        commission = referral_service.handle_purchase_subscription(self.user2, amount_paid)
        self.referral.refresh_from_db()

        self.assertEqual(self.referral.status, ReferralStateChoices.ACTIVE)
        expected_commission_amount = Decimal(amount_paid * (self.commission_rate / 100) / 100)

        self.assertIsNotNone(commission)
        self.assertEqual(commission.amount, expected_commission_amount)
        self.assertEqual(commission.promoter, self.promoter)
        self.assertEqual(commission.referral, self.referral)

    def test_handle_user_refund(self):
        self.referral.status = ReferralStateChoices.ACTIVE
        self.referral.save()

        amount_paid = 15000  # amount in cents
        amount_refunded = 5000  # amount refunded in cents

        initial_commission = promoter_payout_service.create_commission(
            referral=self.referral, amount_paid=amount_paid
        )

        result = referral_service.handle_user_refund(self.user2, amount_refunded=amount_refunded,
                                                     amount_paid=amount_paid)
        self.referral.refresh_from_db()

        expected_refund_amount = -math.floor(initial_commission.amount * amount_refunded / amount_paid)

        self.assertEqual(result.amount, expected_refund_amount)
        self.assertEqual(result.status, PromoterCommissionStatusChoices.REFUND)
        self.assertEqual(self.referral.status, ReferralStateChoices.REFUND)


class PromoterServiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test-user', email='test@example.com', password='Password123')

    def test_create_new_promoter(self):
        promoter = promoter_service.create_new_promoter(user=self.user)

        self.assertIsNotNone(promoter)
        self.assertEqual(promoter.user, self.user)
        self.assertTrue(len(promoter.referral_token) > 0)
        self.assertTrue(promoter.referral_link.startswith(config.BASE_REFERRAL_LINK))

        self.assertTrue(Promoter.objects.filter(user=self.user).exists())

    def test_get_or_create_promoter_existing(self):
        existing_promoter = Promoter.objects.create(
            user=self.user,
            referral_token='existing-token',
            referral_link='http://example.com/referral?ref=existingtoken'
        )

        promoter = promoter_service.get_or_create_promoter(user=self.user)

        self.assertEqual(promoter, existing_promoter)
        self.assertTrue(Promoter.objects.filter(user=self.user).exists())


# ---------------------------------------------------------------------------
# View edge-case tests
# ---------------------------------------------------------------------------

class ViewSetEdgeCaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(
            name='edge_program', commission_rate=20.00, is_active=True, min_withdrawal_balance=10
        )
        cls.user = User.objects.create_user(username='edge-user', email='edge@example.com', password='Pass123')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='edge-token')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.promoter.refresh_from_db()

    def test_set_payout_method_invalid_data_returns_400(self):
        url = reverse('referrals-set-payout-method')
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_payout_method_updates_existing_payout_method(self):
        """Covers the branch where active_payout_method already exists (lines 84-86)."""
        existing_payout = PayoutMethod.objects.create(method='wise', payment_address='old@example.com')
        self.promoter.active_payout_method = existing_payout
        self.promoter.save()

        url = reverse('referrals-set-payout-method')
        data = {'method': 'crypto', 'payment_address': 'new@example.com'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        existing_payout.refresh_from_db()
        self.assertEqual(existing_payout.method, 'crypto')
        self.assertEqual(existing_payout.payment_address, 'new@example.com')

    def test_set_min_withdrawal_balance_invalid_data_returns_400(self):
        url = reverse('referrals-set-min-withdrawal-balance')
        response = self.client.patch(url, {'min_withdrawal_balance': 'not-a-number'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# ReferralService additional tests
# ---------------------------------------------------------------------------

class ReferralServiceEdgeCaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(
            name='rs_program', commission_rate=20.00, is_active=True, min_withdrawal_balance=10
        )
        cls.user = User.objects.create_user(username='rs-user', email='rs@example.com', password='Pass123')
        cls.user2 = User.objects.create_user(username='rs-user2', email='rs2@example.com', password='Pass123')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='rs-token')
        cls.referral = Referral.objects.create(
            user=cls.user2, promoter=cls.promoter, status=ReferralStateChoices.SIGNUP
        )

    @patch.object(_referral_service_module, 'get_template')
    def test_send_referral_invitation_email_success(self, mock_get_template):
        mock_template = MagicMock()
        mock_template.render.return_value = '<html>body</html>'
        mock_get_template.return_value = mock_template

        with patch.object(_referral_service_module, 'EmailMessage') as mock_email_cls:
            mock_email_instance = MagicMock()
            mock_email_cls.return_value = mock_email_instance

            result = referral_service.send_referral_invitation_email(
                emails_to=['recipient@example.com'],
                invitation_link='http://example.com/?ref=TOKEN',
                promoter_full_name='John Doe',
                subject='Join us!',
                template_path='email/referral.html',
            )

        self.assertTrue(result)
        mock_email_instance.send.assert_called_once()

    @patch.object(_referral_service_module, 'get_template')
    def test_send_referral_invitation_email_template_not_found(self, mock_get_template):
        mock_get_template.side_effect = TemplateDoesNotExist('email/missing.html')

        result = referral_service.send_referral_invitation_email(
            emails_to=['recipient@example.com'],
            invitation_link='http://example.com/?ref=TOKEN',
            promoter_full_name='John Doe',
            subject='Join us!',
            template_path='email/missing.html',
        )

        self.assertFalse(result)

    def test_get_referrer_by_user_id_no_referral_relation(self):
        """User exists but has no referral — ObjectDoesNotExist branch."""
        result = referral_service.get_referrer_by_user_id(self.user.id)
        self.assertIsNone(result)

    def test_handle_purchase_subscription_no_referral(self):
        """User has no referral — ObjectDoesNotExist branch (lines 192-193)."""
        result = referral_service.handle_purchase_subscription(self.user, 1000)
        self.assertIsNone(result)

    def test_handle_user_refund_no_referral(self):
        """User has no referral — ObjectDoesNotExist branch (lines 223-224)."""
        result = referral_service.handle_user_refund(self.user, 500, 1000)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# PromoterPayoutService additional tests
# ---------------------------------------------------------------------------

class PromoterPayoutServiceEdgeCaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(
            name='payout_program', commission_rate=20.00, is_active=True, min_withdrawal_balance=10
        )
        cls.user = User.objects.create_user(
            username='payout-user', first_name='Pay', last_name='Out',
            email='payout@example.com', password='Pass123'
        )
        cls.user2 = User.objects.create_user(username='payout-user2', email='payout2@example.com', password='Pass123')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='payout-token')
        cls.referral = Referral.objects.create(
            user=cls.user2, promoter=cls.promoter, status=ReferralStateChoices.SIGNUP
        )

    def setUp(self):
        self.promoter.refresh_from_db()

    def test_send_wise_csv_for_promoters_payouts_eligible_promoter(self):
        """Covers send_wise_csv_for_promoters_payouts main loop (lines 44-63) and helpers.py."""
        payout_method = PayoutMethod.objects.create(method='wise', payment_address='payout@example.com')
        self.promoter.active_payout_method = payout_method
        self.promoter.save()
        # Create a commission so current_balance > 0 and >= min_withdrawal_balance (10)
        PromoterCommission.objects.create(promoter=self.promoter, referral=self.referral, amount=50)

        result = promoter_payout_service.send_wise_csv_for_promoters_payouts()

        self.assertIsNotNone(result)
        self.assertIn('payout@example.com', result)
        # A payout record should have been created
        self.assertTrue(PromoterPayout.objects.filter(promoter=self.promoter, payout_method='wise').exists())

    def test_send_wise_csv_for_promoters_payouts_below_min_balance_returns_none(self):
        """Promoter balance too low — data list stays empty → None."""
        payout_method = PayoutMethod.objects.create(method='wise', payment_address='low@example.com')
        self.promoter.active_payout_method = payout_method
        self.promoter.save()
        # Commission of 5 is below min_withdrawal_balance of 10
        PromoterCommission.objects.create(promoter=self.promoter, referral=self.referral, amount=5)

        result = promoter_payout_service.send_wise_csv_for_promoters_payouts()

        self.assertIsNone(result)

    def test_calculate_commission_no_referral_returns_none(self):
        """User has no referral → early return None (line 84)."""
        result = promoter_payout_service.calculate_commission(self.user.id, 1000)
        self.assertIsNone(result)

    def test_calculate_commission_already_received_returns_none(self):
        """Commission already exists → early return None (lines 90-91)."""
        PromoterCommission.objects.create(promoter=self.promoter, referral=self.referral, amount=30)
        result = promoter_payout_service.calculate_commission(self.user2.id, 1000)
        self.assertIsNone(result)

    def test_create_payout_creates_record_and_marks_commissions_paid(self):
        """Covers create_payout static method (lines 155-160)."""
        commission = PromoterCommission.objects.create(
            promoter=self.promoter, referral=self.referral, amount=50,
            status=PromoterCommissionStatusChoices.PENDING
        )

        promoter_payout_service.create_payout(self.promoter, 50, 'wise')

        self.assertTrue(PromoterPayout.objects.filter(
            promoter=self.promoter, amount=50, payout_method='wise'
        ).exists())
        commission.refresh_from_db()
        self.assertEqual(commission.status, PromoterCommissionStatusChoices.PAID)

    def test_calculate_refund_raises_when_no_commission(self):
        """No positive commission for referral → ViewException (line 182)."""
        with self.assertRaises(ViewException):
            promoter_payout_service.calculate_refund(self.referral, 500, 1000)


# ---------------------------------------------------------------------------
# Repository tests
# ---------------------------------------------------------------------------

class PromoterCommissionRepositoryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(
            name='cr_program', commission_rate=20.00, is_active=True, min_withdrawal_balance=10
        )
        cls.user = User.objects.create_user(username='cr-user', email='cr@example.com', password='Pass123')
        cls.user2 = User.objects.create_user(username='cr-user2', email='cr2@example.com', password='Pass123')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='cr-token')
        cls.referral = Referral.objects.create(
            user=cls.user2, promoter=cls.promoter, status=ReferralStateChoices.ACTIVE
        )

    def test_mark_commission_paid(self):
        commission = PromoterCommission.objects.create(
            promoter=self.promoter, referral=self.referral, amount=100,
            status=PromoterCommissionStatusChoices.PENDING
        )
        promoter_commission_repository.mark_commission_paid(self.promoter)
        commission.refresh_from_db()
        self.assertEqual(commission.status, PromoterCommissionStatusChoices.PAID)

    def test_mark_commission_failed_with_reason(self):
        commission = PromoterCommission.objects.create(
            promoter=self.promoter, referral=self.referral, amount=100,
            status=PromoterCommissionStatusChoices.PENDING
        )
        promoter_commission_repository.mark_commission_failed_with_reason(self.promoter, 'Payment gateway error')
        commission.refresh_from_db()
        self.assertEqual(commission.status, PromoterCommissionStatusChoices.FAILED)
        self.assertEqual(commission.failure_reason, 'Payment gateway error')


class PromoterPayoutRepositoryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(
            name='pr_program', commission_rate=20.00, is_active=True, min_withdrawal_balance=10
        )
        cls.user = User.objects.create_user(username='pr-user', email='pr@example.com', password='Pass123')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='pr-token')

    def test_create_payout(self):
        promoter_payout_repository.create_payout(self.promoter, 75, 'wise', tx_signature='tx999')
        self.assertTrue(PromoterPayout.objects.filter(
            promoter=self.promoter, amount=75, payout_method='wise', tx_signature='tx999'
        ).exists())


class PromoterRepositoryEdgeCaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(
            name='prrepo_program', commission_rate=20.00, is_active=True, min_withdrawal_balance=10
        )
        cls.user = User.objects.create_user(username='prrepo-user', email='prrepo@example.com', password='Pass123')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='prrepo-token')

    def setUp(self):
        self.promoter.refresh_from_db()

    def test_get_by_referral_token_found(self):
        promoter = promoter_repository.get_by_referral_token('prrepo-token')
        self.assertEqual(promoter, self.promoter)

    def test_get_by_referral_token_not_found(self):
        promoter = promoter_repository.get_by_referral_token('nonexistent-token')
        self.assertIsNone(promoter)

    def test_get_wise_payout_promoters(self):
        payout_method = PayoutMethod.objects.create(method='wise', payment_address='repo@example.com')
        self.promoter.active_payout_method = payout_method
        self.promoter.save()

        promoters = list(promoter_repository.get_wise_payout_promoters())
        self.assertIn(self.promoter, promoters)


# ---------------------------------------------------------------------------
# BaseRepository tests
# ---------------------------------------------------------------------------

class BaseRepositoryTestCase(TestCase):
    """Uses PayoutMethod (no FK deps) to exercise every BaseRepository method."""

    def setUp(self):
        self.repo = BaseRepository(model=PayoutMethod)

    def _make(self, method='wise', address='a@test.com'):
        return PayoutMethod.objects.create(method=method, payment_address=address)

    def test_get_one_found(self):
        obj = self._make()
        result = self.repo.get_one(pk=obj.pk)
        self.assertEqual(result, obj)

    def test_get_one_not_found(self):
        result = self.repo.get_one(pk=99999)
        self.assertIsNone(result)

    def test_get_all(self):
        self._make('wise', 'a@test.com')
        self._make('crypto', 'b@test.com')
        self.assertEqual(self.repo.get_all().count(), 2)

    def test_get_or_create_creates(self):
        obj, created = self.repo.get_or_create(
            defaults={'payment_address': 'c@test.com'}, method='paypal'
        )
        self.assertTrue(created)
        self.assertEqual(obj.method, 'paypal')

    def test_get_or_create_existing(self):
        existing = self._make('stripe', 'stripe@test.com')
        obj, created = self.repo.get_or_create(
            defaults={'payment_address': 'other@test.com'}, method='stripe', payment_address='stripe@test.com'
        )
        self.assertFalse(created)
        self.assertEqual(obj.pk, existing.pk)

    def test_create_many(self):
        items = [
            {'method': 'a', 'payment_address': 'a@x.com'},
            {'method': 'b', 'payment_address': 'b@x.com'},
        ]
        results = self.repo.create_many(items)
        self.assertEqual(len(results), 2)

    def test_update(self):
        obj = self._make()
        updated = self.repo.update({'payment_address': 'updated@test.com'}, pk=obj.pk)
        self.assertEqual(updated.payment_address, 'updated@test.com')

    def test_update_or_create_creates(self):
        obj, created = self.repo.update_or_create(
            defaults={'payment_address': 'new@test.com'}, method='newmethod'
        )
        self.assertTrue(created)

    def test_update_or_create_updates(self):
        existing = self._make('updateme', 'old@test.com')
        obj, created = self.repo.update_or_create(
            defaults={'payment_address': 'new@test.com'}, method='updateme'
        )
        self.assertFalse(created)
        self.assertEqual(obj.payment_address, 'new@test.com')

    def test_exclude(self):
        self._make('wise', 'a@test.com')
        self._make('crypto', 'b@test.com')
        result = self.repo.exclude(method='wise')
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().method, 'crypto')

    def test_select_for_update(self):
        self._make()
        with transaction.atomic():
            qs = self.repo.select_for_update()
            self.assertEqual(qs.count(), 1)

    def test_filter_one(self):
        obj = self._make('filterme', 'f@test.com')
        result = self.repo.filter_one(method='filterme')
        self.assertEqual(result, obj)

    def test_filter_one_not_found(self):
        result = self.repo.filter_one(method='doesnotexist')
        self.assertIsNone(result)

    def test_delete_by_obj(self):
        obj = self._make()
        deleted = self.repo.delete(db_obj=obj)
        self.assertTrue(deleted)
        self.assertEqual(PayoutMethod.objects.filter(pk=obj.pk).count(), 0)

    def test_delete_by_filter(self):
        self._make('delme', 'd@test.com')
        deleted = self.repo.delete(method='delme')
        self.assertTrue(deleted)
        self.assertFalse(PayoutMethod.objects.filter(method='delme').exists())

    def test_select_related(self):
        # PayoutMethod has no relations; verify it returns a queryset without error
        self._make()
        qs = self.repo.select_related()
        self.assertGreaterEqual(qs.count(), 1)

    def test_prefetch_related(self):
        self._make()
        qs = self.repo.prefetch_related()
        self.assertGreaterEqual(qs.count(), 1)

    def test_bulk_create(self):
        objs = [PayoutMethod(method='bc1', payment_address='bc1@test.com'),
                PayoutMethod(method='bc2', payment_address='bc2@test.com')]
        results = self.repo.bulk_create(objs)
        self.assertEqual(len(results), 2)

    def test_bulk_update(self):
        obj = self._make('bu', 'bu@test.com')
        obj.payment_address = 'updated@test.com'
        self.repo.bulk_update([obj], fields=['payment_address'])
        obj.refresh_from_db()
        self.assertEqual(obj.payment_address, 'updated@test.com')

    def test_values_list(self):
        self._make('vl', 'vl@test.com')
        methods = list(self.repo.values_list('method', flat=True))
        self.assertIn('vl', methods)


# ---------------------------------------------------------------------------
# Serializer additional tests
# ---------------------------------------------------------------------------

class SerializerEdgeCaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.referral_program = ReferralProgram.objects.create(
            name='ser_program', commission_rate=20.00, is_active=True, min_withdrawal_balance=10
        )
        cls.user = User.objects.create_user(username='ser-user', email='ser@example.com', password='Pass123')
        cls.user2 = User.objects.create_user(username='ser-user2', email='ser2@example.com', password='Pass123')
        cls.promoter = Promoter.objects.create(user=cls.user, referral_token='ser-token')
        cls.referral = Referral.objects.create(
            user=cls.user2, promoter=cls.promoter, status=ReferralStateChoices.ACTIVE
        )

    def test_get_current_user_with_request(self):
        """CamelCaseSerializer.get_current_user returns user from request context (lines 16-20)."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.user
        serializer = ReferralSerializer(context={'request': request})
        self.assertEqual(serializer.get_current_user(), self.user)

    def test_get_current_user_without_request(self):
        serializer = ReferralSerializer(context={})
        self.assertIsNone(serializer.get_current_user())

    def test_referral_serializer_commission_amount_and_status_when_commission_exists(self):
        """Covers lines 65 and 71: commission.amount and commission.status returned."""
        commission = PromoterCommission.objects.create(
            promoter=self.promoter, referral=self.referral, amount=42,
            status=PromoterCommissionStatusChoices.PENDING
        )
        data = ReferralSerializer(self.referral).data
        self.assertEqual(data['commissionAmount'], 42)
        self.assertEqual(data['commissionStatus'], PromoterCommissionStatusChoices.PENDING)


# ---------------------------------------------------------------------------
# Utils, helpers, decorators, enums, and model tests
# ---------------------------------------------------------------------------

class UtilsTestCase(TestCase):
    def test_append_query_params_new_key(self):
        url = append_query_params('http://example.com/', {'ref': 'TOKEN'})
        self.assertIn('ref=TOKEN', url)

    def test_append_query_params_existing_key_merges_values(self):
        """Covers the list-merge branch (lines 20-23)."""
        url = 'http://example.com/?ref=FIRST'
        result = append_query_params(url, {'ref': 'SECOND'})
        self.assertIn('FIRST', result)
        self.assertIn('SECOND', result)

    def test_append_query_params_multiple_new_keys(self):
        url = append_query_params('http://example.com/', {'ref': 'A', 'ref-source': 'email'})
        self.assertIn('ref=A', url)
        self.assertIn('ref-source=email', url)


class HelpersTestCase(TestCase):
    def test_parse_df_to_csv_string_without_index_col(self):
        df = pd.DataFrame({'name': ['Alice', 'Bob'], 'amount': [10, 20]})
        csv_string = parse_df_to_csv_string_without_index_col(df)
        self.assertIn('name,amount', csv_string)
        self.assertIn('Alice', csv_string)
        self.assertIn('Bob', csv_string)
        # No index column
        self.assertNotIn(',0,', csv_string)
        self.assertNotIn(',1,', csv_string)


class DecoratorsTestCase(TestCase):
    def test_sync_to_async_wraps_sync_function(self):
        """Sync functions should be dispatched through the event loop executor."""
        def my_sync(self, x):
            return x * 2

        wrapped = sync_to_async(my_sync)

        async def run_test():
            future = asyncio.get_running_loop().create_future()
            future.set_result(42)

            with patch('referrals.repositories.decorators.asyncio.get_running_loop') as mock_get_loop:
                mock_loop = MagicMock()
                mock_loop.run_in_executor.return_value = future
                mock_get_loop.return_value = mock_loop

                result = await wrapped(None, 21)

            self.assertEqual(result, 42)
            mock_loop.run_in_executor.assert_called_once()

        asyncio.run(run_test())

    def test_sync_to_async_wraps_async_function(self):
        """Already-async function is awaited directly (line 18)."""
        async def my_async(self, x):
            return x + 1

        wrapped = sync_to_async(my_async)
        result = asyncio.run(wrapped(None, 9))
        self.assertEqual(result, 10)


class EnumsTestCase(TestCase):
    def test_referral_state_enum_values(self):
        self.assertEqual(ReferralStateEnum.SIGNUP.value, 'signup')
        self.assertEqual(ReferralStateEnum.ACTIVE.value, 'active')

    def test_payout_status_enum_values(self):
        self.assertEqual(PayoutStatusEnum.PENDING.value, 'pending')
        self.assertEqual(PayoutStatusEnum.COMPLETED.value, 'completed')
        self.assertEqual(PayoutStatusEnum.PROCESSING.value, 'processing')

    def test_crypto_payout_token_ids_enum_values(self):
        self.assertEqual(CryptoPayoutTokenIdsEnum.USDC.value, 'usd-coin')


class ModelStrTestCase(TestCase):
    def test_payout_method_str(self):
        pm = PayoutMethod(method='wise', payment_address='x@y.com')
        self.assertEqual(str(pm), 'wise')

    def test_promoter_str(self):
        user = User.objects.create_user(username='model-user', email='model@example.com', password='Pass123')
        promoter = Promoter.objects.create(
            user=user,
            referral_token='model-token',
            referral_link='https://example.com/ref?ref=model-token',
        )

        self.assertEqual(str(promoter), 'model@example.com - https://example.com/ref?ref=model-token')
