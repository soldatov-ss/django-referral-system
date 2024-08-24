from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from referrals.models import ReferralProgram, Promoter


class ReferralProgramViewSetTestCase(APITestCase):
    def setUp(self):
        self.referral_program = ReferralProgram.objects.create(name='test_program', commission_rate=20.00,
                                                               is_active=True, min_withdrawal_balance=10)
        self.user = User.objects.create_user(username='test-user', email='test@example.com', password='Password123')
        self.user2 = User.objects.create_user(username='test-user2', email='test2@example.com', password='Password321')

        self.promoter = Promoter.objects.create(user=self.user2)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_referral_link(self):
        url = reverse('referrals-get-referral-link')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Promoter.objects.filter(user=self.user).exists())

        self.assertIn('referralLink', response.data)
        self.assertEqual(response.data['referralLink'], self.user.promoter.referral_link)

    def test_set_payout_method_to_promoter(self):
        self.client.force_authenticate(user=self.user2)

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

    def tearDown(self):
        self.user.delete()
        self.referral_program.delete()
