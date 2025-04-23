from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from database import Base


class ResourceType(str, enum.Enum):
    room = "room"
    equipment = "equipment"


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    resource_type = Column(Enum(ResourceType), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, default="active")
