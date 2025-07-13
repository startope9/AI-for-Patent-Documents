# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import os

from app.routes import auth, chat, topic  # <- added topic

# === ENVIRONMENT SETUP ===
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")

# === INIT FASTAPI ===
app = FastAPI(
    title="PatentAI",
    description="API for user auth, topic-based patent parsing, vectorization, and LLM chat",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend dev origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DB CLIENTS ===
mongo_client = AsyncIOMotorClient(MONGO_URI)
redis_client = redis.from_url(REDIS_URI, decode_responses=True)

# === SHARED STATE ===
app.state.mongo = mongo_client.patentbot
app.state.redis = redis_client

# === INCLUDE ROUTERS ===
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(topic.router, prefix="/api", tags=["Topic"])
