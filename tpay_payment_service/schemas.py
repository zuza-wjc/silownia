from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import List


class KafkaProduct(BaseModel):
    price: float


class KafkaCustomer(BaseModel):
    email: EmailStr


class KafkaPaymentEvent(BaseModel):
    internalId: str
    description: str
    customer: KafkaCustomer
    products: List[KafkaProduct] = Field(..., min_items=1)


class PaymentMethod(str, Enum):
    tpay = "TPay"
    payu = "PayU"

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            raise ValueError("Invalid type for payment method")

        normalized = value.strip().replace(" ", "").lower()
        mapping = {
            "tpay": cls.tpay,
            "payu": cls.payu,
        }
        try:
            return mapping[normalized]
        except KeyError:
            raise ValueError(f"Invalid payment method: {value}")


class CreatePaymentRequest(BaseModel):
    email: str
    amount: float
    description: str


class PaymentResponse(BaseModel):
    payment_url: str
    transaction_id: str
    transaction_title: str