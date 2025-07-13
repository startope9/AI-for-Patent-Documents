# app/routes/chat.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
async def chat_with_ai(request: Request, data: ChatRequest):
    redis_client = request.app.state.redis
    user_email = await redis_client.get(data.session_id)

    if not user_email:
        raise HTTPException(
            status_code=401, detail="Session expired or invalid")

    from app.chat_interface import run_query
    answer, pids = await run_query(data.message)

    return {
        "answer": answer,
        "citations": pids,
        "user": user_email
    }
