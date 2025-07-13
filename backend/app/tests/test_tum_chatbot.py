"""Test the accuracy of the chatbot when asked TUM programs related question"""
import asyncio
import json
import os
import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.tests.test_chatbot_agent import test_chatbot_agent
from app.config import settings


os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY


async def call_test_chatbot_agent():
    """Run test_chatbot_agent agent"""

    # Set up session service and runner
    user_id = "user_1"
    session_id = "session_generate_001"
    app_name = "generate_app"
    session_service = InMemorySessionService()

    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

    runner = Runner(
        agent=test_chatbot_agent,
        app_name=app_name,
        session_service=session_service
    )

    # Send a single request to generate 100 questions
    print("Sending prompt to generate questions...")
    user_input = "Please test the LLM-based chatbot for answer Technical University of Munich (TUM) related questions"
    content = types.Content(role="user", parts=[types.Part(text=user_input)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print("✅ Final response received.")
                print(f"Response: {response_text}")
                break
            else:
                print("⚠️ Final response was empty.")

if __name__ == "__main__":
    asyncio.run(call_test_chatbot_agent())
