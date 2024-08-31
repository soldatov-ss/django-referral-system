import math
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from referrals.choices import InvitationMethodChoices, ReferralStateChoices, PromoterCommissionStatusChoices
from referrals.config import config
from referrals.exceptions import ViewException
from referrals.models import ReferralProgram, Promoter, Referral, PromoterPayout, PromoterCommission
from referrals.serializers import ReferralSerializer, PromoterSerializer, PromoterPayoutsSerializer
from referrals.services import referral_service, promoter_service
from referrals.services.promoter_payout_service import promoter_payout_service


class ReferralProgramViewSetTestCase(APITestCase):
    def setUp(self):
        self.referral_program = ReferralProgram.objects.create(name='test_program', commission_rate=20.00,
                                                               is_active=True, min_withdrawal_balance=10)
        self.user = User.objects.create_user(username='test-user', email='test@example.com', password='Password123')
        self.user2 = User.objects.create_user(username='test-user2', email='test2@example.com', password='Password321')
        self.user3 = User.objects.create_user(username='test-user3', email='test3@example.com', password='Password121')
        self.user4 = User.objects.create_user(username='test-user4', email='test4@example.com', password='Password111')

        self.promoter = Promoter.objects.create(user=self.user, referral_token='test-token')

        self.referral = Referral.objects.create(
            user=self.user2,
            promoter=self.promoter,
            status=ReferralStateChoices.ACTIVE
        )
        self.referral2 = Referral.objects.create(
            user=self.user3,
            promoter=self.promoter,
            status=ReferralStateChoices.ACTIVE
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

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
        seven_days_ago = datetime.today().date() - timedelta(days=6)
        PromoterCommission.objects.create(promoter=self.promoter, amount=100, referral=self.referral,
                                          created=seven_days_ago)
        PromoterCommission.objects.create(promoter=self.promoter, amount=200, referral=self.referral2,
                                          created=datetime.today())

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

    def tearDown(self):
        ReferralProgram.objects.all().delete()
        Promoter.objects.all().delete()
        Referral.objects.all().delete()
        PromoterPayout.objects.all().delete()
        PromoterCommission.objects.all().delete()
        User.objects.all().delete()


class ReferralServiceTestCase(TestCase):
    commission_rate = 20.00

    def setUp(self):
        self.referral_program = ReferralProgram.objects.create(name='test_program',
                                                               commission_rate=self.commission_rate,
                                                               is_active=True, min_withdrawal_balance=10)
        self.user = User.objects.create_user(username='test-user', email='test@example.com', password='Password123')
        self.user2 = User.objects.create_user(username='test-user2', email='test2@example.com', password='Password321')
        self.user3 = User.objects.create_user(username='test-user3', email='test3@example.com', password='Password121')

        self.promoter = Promoter.objects.create(user=self.user, referral_token='test-token')
        self.referral = Referral.objects.create(
            user=self.user2,
            promoter=self.promoter,
            status=ReferralStateChoices.SIGNUP
        )
        self.referral2 = Referral.objects.create(
            user=self.user3,
            promoter=self.promoter,
            status=ReferralStateChoices.SIGNUP
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_user_earnings(self):
        seven_days_ago = datetime.today().date() - timedelta(days=6)
        PromoterCommission.objects.create(promoter=self.promoter, referral=self.referral, amount=100,
                                          created=seven_days_ago)
        PromoterCommission.objects.create(promoter=self.promoter, referral=self.referral2, amount=200,
                                          created=datetime.today())

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

    def tearDown(self):
        User.objects.all().delete()
        ReferralProgram.objects.all().delete()
        Promoter.objects.all().delete()
        Referral.objects.all().delete()
        PromoterCommission.objects.all().delete()


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

    @classmethod
    def tearDownClass(cls):
        Promoter.objects.all().delete()
        User.objects.all().delete()
