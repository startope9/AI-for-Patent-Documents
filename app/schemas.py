# app/schemas.py
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class SessionAuth(BaseModel):
    session_id: str = Field(..., min_length=36, max_length=36)  # UUID4

class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=36, max_length=36)
    message: str = Field(..., min_length=1)

class TopicInitRequest(BaseModel):
    topic: str = Field(..., strip_whitespace=True, min_length=1, max_length=100)
