# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from uuid import uuid4
import os

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# === MODELS ===
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionAuth(BaseModel):
    session_id: str


# === UTILS ===
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def generate_session_id() -> str:
    return str(uuid4())


# === DEPENDENCY ===
async def get_current_user(request: Request, session: SessionAuth) -> str:
    redis_client = request.app.state.redis
    user_email = await redis_client.get(session.session_id)
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return user_email


# === ROUTES ===
@router.post("/register")
async def register_user(request: Request, data: RegisterRequest):
    db = request.app.state.mongo
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(data.password)
    await db.users.insert_one({"email": data.email, "password": hashed_pw})
    return {"message": "User registered successfully"}


@router.post("/login")
async def login_user(request: Request, data: LoginRequest):
    print("DEBUG_MONGO_URI", os.getenv("MONGO_URI"))
    db = request.app.state.mongo
    redis_client = request.app.state.redis

    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = generate_session_id()
    await redis_client.set(session_id, user["email"], ex=86400)  # 1 day expiry
    return {"message": "Login successful", "session_id": session_id}
