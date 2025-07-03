from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import EmailRequest, EmailResponse
from app.services.email_service import EmailAgent
from app.utils.supabase_auth import verify_supabase_token

router = APIRouter(
    prefix="/api",
    tags=["email"],
)

# Create a single instance for the email agent
email_agent_instance = EmailAgent()
runner_initialized = False

# Initialize the session and runner, which necessitate for calling the Email Agent
@router.on_event("startup")
async def startup_event():
    global runner_initialized
    if not runner_initialized:
        await email_agent_instance.initialize_runner()
        runner_initialized = True


@router.post("/email", response_model=EmailResponse)
async def send_email_via_agent(
    request: EmailRequest
):
    """
    Trigger the Email Agent to send an escalation or notify human staff.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        response = await email_agent_instance.call_agent_async(request.question)
        return EmailResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))