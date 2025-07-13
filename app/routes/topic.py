# app/routes/topic.py
import os
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.routes.auth import get_current_user
from app.utils.patent_parser import parse_and_save_topic
from app.utils.vector_uploader import load_csv_to_vectordb

router = APIRouter()

class TopicInitRequest(BaseModel):
    topic: str

@router.post("/topic/initiate")
async def initiate_topic(
    request: Request,
    req: TopicInitRequest,
    user_email: str = Depends(get_current_user)
):
    topic = req.topic.strip().lower().replace(" ", "_")

    parsed_dir = os.path.join(os.path.dirname(__file__), "..", "parsed_patents")
    os.makedirs(parsed_dir, exist_ok=True)
    csv_file = os.path.join(parsed_dir, f"{topic}_50patents.csv")

    if os.path.exists(csv_file):
        return {
            "status": "exists",
            "message": f"Topic '{topic}' already parsed and stored.",
            "user": user_email
        }

    # Step 1: Parse and save
    try:
        csv_path = parse_and_save_topic(topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

    # Step 2: Insert into vector DB
    try:
        count = load_csv_to_vectordb(csv_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector DB insert failed: {str(e)}")

    return {
        "status": "success",
        "message": f"Inserted {count} patents for topic '{topic}' into ChromaDB.",
        "user": user_email
    }
