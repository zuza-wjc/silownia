from fastapi import FastAPI, Depends, HTTPException
from auth import register_user, login_user
from database import Base, engine
from models import UserProfile
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
from schemas import UserRegister, UserAuth, UserResponse

app = FastAPI()

Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
async def register(data: UserRegister, db: Session = Depends(get_db)):
    await register_user(data.email, data.password)

    user = crud.create_user_profile(
        db=db,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        birth_date=data.birth_date,
        address=data.address
    )
    return {"message": "Rejestracja zakończona", "user": user.email}

@app.post("/login")
async def login(data: UserAuth):
    return await login_user(data.email, data.password)


@app.get("/user", response_model=UserResponse)
def get_user(email: str, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    return user