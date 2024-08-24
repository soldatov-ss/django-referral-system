from datetime import datetime
from typing import List, Optional

from pydantic import Field

from referrals.dtos.base_dto import BaseModelDTO
from referrals.enums import PayoutStatusEnum


class PromotionDTO(BaseModelDTO):
    id: int
    ref_id: str = Field(alias="refId")
    promoter_id: int = Field(alias="promoterId")
    referral_link: str = Field(alias="referralLink")
    visitors_count: int = Field(alias="visitorsCount")
    leads_count: int = Field(alias="leadsCount")
    customers_count: int = Field(alias="customersCount")
    refunds_count: int = Field(alias="refundsCount")
    cancellations_count: int = Field(alias="cancellationsCount")


class BalanceDTO(BaseModelDTO):
    cash: int


class PromoterDTO(BaseModelDTO):
    id: int
    status: str
    cust_id: Optional[str] = Field(alias="custId")
    email: str
    created_at: datetime = Field(alias="createdAt")
    promotions: List[PromotionDTO]
    earnings_balance: Optional[BalanceDTO] = Field(alias="earningsBalance")
    current_balance: Optional[BalanceDTO] = Field(alias="currentBalance")
    paid_balance: Optional[BalanceDTO] = Field(alias="paidBalance")


class ReferralDTO(BaseModelDTO):
    id: int
    state: str
    email: str
    promotion: PromotionDTO
    promoter: PromoterDTO


class ReferralListDTO(BaseModelDTO):
    count: int | None
    page_size: int
    page: int
    results: List[ReferralDTO]


class PromoterPayoutDTO(BaseModelDTO):
    status: PayoutStatusEnum
    amount: int
    unit: str
    created_at: str = Field(alias="createdAt")
    date_paid: str | None = Field(default=None, alias="datePaid")
    due_date: str | None = Field(default=None, alias="dueDate")


class PromoterCryptoPayoutDataRow(BaseModelDTO):
    name: str
    email: str
    address: str
    amount: float
