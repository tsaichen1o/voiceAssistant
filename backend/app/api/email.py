from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict, Any

from app.services.email_service import send_inquiry_email
from app.services.session_service import get_session
from app.utils.supabase_auth import verify_supabase_token


router = APIRouter(
    prefix="/api/email",
    tags=["email"],
)

class EmailSendRequest(BaseModel):
    user_email: EmailStr
    session_id: str

@router.post("/send")
async def send_email_from_user(
    request: EmailSendRequest,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    user_id = user_info.get("sub")

    session_data = get_session(session_id=request.session_id, user_id=user_id)
    if not session_data or not session_data.get("messages"):
        raise HTTPException(status_code=404, detail="Chat history not found for this session.")

    full_chat_history = session_data["messages"]
    
    last_user_message = next((msg for msg in reversed(full_chat_history) if msg["role"] == "user"), None)
    
    if not last_user_message:
        raise HTTPException(status_code=400, detail="No user question found in history.")
    last_question = last_user_message["content"]

    context_messages = full_chat_history[-5:]

    chat_history_str = "\n".join(
        f"[{msg['role']}] {msg['content']}" for msg in context_messages
    )

    result = send_inquiry_email(
        user_email=request.user_email,
        user_question=last_question,
        chat_history_str=chat_history_str
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return {"message": "Inquiry sent successfully. A staff member will contact you via email shortly."}