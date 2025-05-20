from sqlalchemy import Column, Integer, String, Date
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

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    expiration_date = Column(Date)
    status = Column(String)     # 'inactive', 'paid', 'active'

class Trainers(Base):
    __tablename__ = "trainers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)    

class RegistrationRequest(BaseModel):
    client_id: str
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
