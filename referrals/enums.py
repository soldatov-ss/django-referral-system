from enum import Enum


class ReferralStateEnum(Enum):
    SIGNUP = "signup"
    INVITED = "invited"
    ACTIVE = "active"


class PayoutStatusEnum(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    PROCESSING = "processing"


class CryptoPayoutTokenIdsEnum(Enum):
    USDC = "usd-coin"
