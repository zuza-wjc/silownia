from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from models import ResourceType


class ReservationCreate(BaseModel):
    user_id: UUID
    resource_type: ResourceType
    resource_id: UUID
    start_time: datetime
    end_time: datetime


class ReservationOut(ReservationCreate):
    id: UUID
    status: str

    class Config:
        orm_mode = True
