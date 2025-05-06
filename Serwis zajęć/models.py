from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class ClassGroup(Base):
    __tablename__ = 'classgroups'
    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer)
    title = Column(String)
    capacity = Column(Integer)
    user_ids = Column(String, default="")

class RegistrationRequest(BaseModel):
    client_email: str
    class_id: int

class CreateClassRequest(BaseModel):
    trainer_id: int
    title: str
    capacity: int

class CancelClassRequest(BaseModel):
    class_id: int

class User(BaseModel):
    name: str
    id: str

class ClassEnrollmentRequest(BaseModel):
    trainer_id: int
    new_user_id: int
