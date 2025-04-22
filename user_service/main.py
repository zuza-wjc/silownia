from fastapi import FastAPI
from pydantic import BaseModel
from auth import register_user, login_user

app = FastAPI()

class UserAuth(BaseModel):
    email: str
    password: str

@app.post("/register")
async def register(data: UserAuth):
    return await register_user(data.email, data.password)

@app.post("/login")
async def login(data: UserAuth):
    return await login_user(data.email, data.password)