from sqlalchemy import Column, Integer, String, Date, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    type = Column(String)
    purchase_date = Column(Date)
    active = Column(String)     # 'inactive', 'paid', 'active'

    __table_args__ = (
        CheckConstraint("type IN ('1m', '3m', '12m')", name="valid_membership_type"),
    )

class MembershipType(str, Enum):
    one_month = "1m"
    three_months = "3m"
    twelve_months = "12m"