from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from referrals.choices import InvitationMethodChoices, ReferralStateChoices
from referrals.exceptions import ViewException
from referrals.models import ReferralProgram, Promoter, Referral, PromoterPayout
from referrals.serializers import ReferralSerializer, PromoterSerializer, PromoterPayoutsSerializer


class ReferralProgramViewSetTestCase(APITestCase):
    def setUp(self):
        self.referral_program = ReferralProgram.objects.create(name='test_program', commission_rate=20.00,
                                                               is_active=True, min_withdrawal_balance=10)
        self.user = User.objects.create_user(username='test-user', email='test@example.com', password='Password123')
        self.user2 = User.objects.create_user(username='test-user2', email='test2@example.com', password='Password321')

        self.promoter = Promoter.objects.create(user=self.user, referral_token='test-token')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_referral_success(self):
        url = reverse('referrals-list')
        data = {
            "email": self.user2.email,
            "referral_token": "test-token",
            "referral_source": InvitationMethodChoices.EMAIL.value,
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Referral.objects.filter(user=self.user2).exists())

        referral = Referral.objects.get(user=self.user2)
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
            "email": self.user2.email,
            "referral_token": "invalid-token",  # Invalid token
            "referral_source": InvitationMethodChoices.LINK.value,
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Referral.objects.filter(user=self.user2).exists())

    def test_list_referrals(self):
        self.referral1 = Referral.objects.create(
            user=self.user,
            promoter=self.promoter,
            invitation_method=InvitationMethodChoices.EMAIL,
            status=ReferralStateChoices.ACTIVE,
            commission_rate=5.00
        )
        self.referral2 = Referral.objects.create(
            user=self.user2,
            promoter=self.promoter,
            invitation_method=InvitationMethodChoices.LINK,
            status=ReferralStateChoices.REFUND,
            commission_rate=7.50
        )

        url = reverse('referrals-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

        expected_data = ReferralSerializer([self.referral1, self.referral2], many=True).data

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

    def tearDown(self):
        User.objects.all().delete()
        ReferralProgram.objects.all().delete()
        Promoter.objects.all().delete()
        Referral.objects.all().delete()
        PromoterPayout.objects.all().delete()
