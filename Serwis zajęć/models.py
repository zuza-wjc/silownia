from sqlalchemy import Column, Integer, String, ForeignKey, Table, Date
from sqlalchemy.orm import relationship, declarative_base
from pydantic import BaseModel

Base = declarative_base()

association_table = Table(
    'association', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id')),
    Column('classgroup_id', Integer, ForeignKey('classgroups.id'))
)

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    valid_until = Column(Date)
    classes = relationship("ClassGroup", secondary=association_table, back_populates="participants")

class ClassGroup(Base):
    __tablename__ = 'classgroups'
    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer)
    title = Column(String)
    capacity = Column(Integer)
    participants = relationship("Client", secondary=association_table, back_populates="classes")

class RegistrationRequest(BaseModel):
    client_id: int
    class_id: int

class User(BaseModel):
    name: str
    id: str

class ClassEnrollmentRequest(BaseModel):
    trainer_id: int
    new_user_id: int
