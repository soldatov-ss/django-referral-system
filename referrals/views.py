import logging

from django.contrib.auth.models import User
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from referrals.choices import (
    InvitationMethodChoices,
    ReferralStateChoices,
)
from referrals.exceptions import ViewException
from referrals.models import PayoutMethod, PromoterPayout, ReferralProgram
from referrals.repositories.promoter_repository import promoter_repository
from referrals.repositories.referral_repository import referral_repository
from referrals.serializers import (
    PayoutMethodSerializer,
    PromoterPayoutsSerializer,
    PromoterSerializer,
    ReferralSerializer, MinWithdrawalBalanceSerializer,
)
from referrals.services import promoter_service, referral_service

logger = logging.getLogger(__name__)


class ReferralsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "pages": self.page.paginator.num_pages,
                "results": data,
            }
        )


class ReferralProgramViewSet(
    viewsets.GenericViewSet,
):
    pagination_class = ReferralsPagination
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        allow_any_actions = ["create", "increment_link_clicked"]
        if self.action in allow_any_actions:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        return referral_repository.get_referrals_by_user_id(self.request.user.id)

    @action(detail=False, methods=["GET"], url_path="get-referral-link")
    def get_referral_link(self, request, *args, **kwargs):
        user = request.user
        promoter = promoter_service.get_or_create_promoter(user=user)
        return Response({"referralLink": promoter.referral_link}, status=HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="promoter")
    def retrieve_promoter(self, request, *args, **kwargs):
        user = request.user
        promoter = promoter_service.get_or_create_promoter(user=user)
        serializer = PromoterSerializer(promoter)
        return Response(serializer.data)

    @action(detail=False, methods=["PATCH"], url_path="set-payout-method")
    def set_payout_method(self, request, *args, **kwargs):
        promoter = request.user.promoter

        serializer = PayoutMethodSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        method = serializer.validated_data.get("method")
        payment_address = serializer.validated_data.get("payment_address")

        if promoter.active_payout_method:
            promoter.active_payout_method.method = method
            promoter.active_payout_method.payment_address = payment_address
            promoter.active_payout_method.save()
        else:
            payout_method = PayoutMethod.objects.create(method=method, payment_address=payment_address)
            promoter.active_payout_method = payout_method
            promoter.save()

        promoter_serializer = PromoterSerializer(promoter)

        return Response(promoter_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["PATCH"], url_path="set-min-withdrawal-balance")
    def set_min_withdrawal_balance(self, request, *args, **kwargs):
        promoter = request.user.promoter

        serializer = MinWithdrawalBalanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        min_withdrawal_balance = serializer.validated_data.get("min_withdrawal_balance")
        program_min_withdrawal_balance = ReferralProgram.get_active_referral_program().min_withdrawal_balance

        if min_withdrawal_balance < program_min_withdrawal_balance:
            raise ViewException(
                f"Min withdrawal balance must be greater than or equal to the referral program's min withdrawal balance ({program_min_withdrawal_balance}).",
                status_code=400)

        promoter.min_withdrawal_balance = min_withdrawal_balance
        promoter.save()

        promoter_serializer = PromoterSerializer(promoter)
        return Response(promoter_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="promoter-recent-earnings")
    def promoter_recent_earnings(self, request, *args, **kwargs):
        user = request.user

        earnings = referral_service.get_user_earnings(user)
        result = referral_service.get_last_7_days_earnings(earnings)
        return Response(result, status=HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="payouts")
    def promoter_payment_history(self, request, *args, **kwargs):
        user = request.user

        payouts = PromoterPayout.objects.filter(promoter__user=user).order_by("-created")
        serializer = PromoterPayoutsSerializer(payouts, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """List referrals objects"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        user = request.user
        promoter_service.get_or_create_promoter(user=user)

        serializer = self.get_serializer(page, many=True)
        response_data = self.get_paginated_response(serializer.data).data
        response_data.setdefault("results", [])

        return Response(response_data, status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Creates a new referral object."""
        user = User.objects.get(email=request.data["email"])

        referral_token: str = request.data.get("referral_token")
        invitation_method: str = request.data.get("referral_source", InvitationMethodChoices.LINK.value)
        promoter = promoter_repository.get_object_or_404(referral_token=referral_token)

        if promoter.user == user:
            raise ViewException("You can't refer to yourself.", status_code=400)

        referral = referral_repository.create(
            user=user,
            promoter=promoter,
            invitation_method=invitation_method if invitation_method else InvitationMethodChoices.LINK.value,
            status=ReferralStateChoices.SIGNUP.value,
        )
        serializer = self.get_serializer(referral)
        return Response(serializer.data, status=HTTP_201_CREATED)

    @action(detail=False, methods=["POST"], url_path="increment-link-clicked")
    def increment_link_clicked(self, request, *args, **kwargs):
        referral_token = request.data.get("referral_token")
        promoter = promoter_repository.get_object_or_404(referral_token=referral_token)

        promoter.link_clicked = promoter.link_clicked + 1
        promoter.save()
        return Response({"message": "Link clicked count incremented successfully"}, status=status.HTTP_200_OK)
