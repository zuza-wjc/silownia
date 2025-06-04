from datetime import date
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class PaymentStatus(str, Enum):
    created = "created"
    success = "success"
    failed = "failed"

class PaymentMethod(str, Enum):
    tpay = "TPay"
    payu = "PayU"

    @classmethod
    def _missing_(cls, value):
        normalized_value = value.strip().replace(" ", "").lower()

        if normalized_value == "tpay":
            return cls.tpay
        elif normalized_value == "payu":
            return cls.payu
        else:
            raise ValueError(f"Invalid payment method: {value}")


class Customer(BaseModel):
    id: str
    ip: str
    email: str
    firstName: str
    lastName: str


class Product(BaseModel):
    name: str
    price: float


class CreatePaymentRequest(BaseModel):
    internalId: str
    description: str
    customer: Customer
    products: List[Product]


class PaymentStatusNotification(BaseModel):
    orderId: str
    extOrderId: str
    status: PaymentStatus


class MembershipResponse(BaseModel):
    email: str
    status: str

class MembershipDateResponse(BaseModel):
    email: str
    status: str
    type: str
    expiration_date: Optional[date]

    class Config:
        orm_mode = True

class BuyMembershipResponse(BaseModel):
    message: str
    membership: MembershipResponse
    redirect: Optional[str] = None


class VerifyMembershipResponse(BaseModel):
    message: str