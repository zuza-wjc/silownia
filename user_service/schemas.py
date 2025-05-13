from pydantic import BaseModel
from datetime import date

class UserRegister(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    birth_date: date
    address: str

class UserAuth(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    email: str
    first_name: str
    last_name: str
    birth_date: date
    address: str