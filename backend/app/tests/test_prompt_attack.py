"""Test the accuracy of the chatbot when asked TUM programs related question"""
import asyncio
import json
import os
import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.tests.prompt_attack_agent import prompt_injection_agent, prompt_leaking_agent, jailbreaking_agent
from app.config import settings


os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY


async def call_prompt_injection_agent():
    """Run prompt_injection_agent agent"""

    # Set up session service and runner
    user_id = "user_1"
    session_id = "session_generate_001"
    app_name = "generate_app"
    session_service = InMemorySessionService()

    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

    runner = Runner(
        agent=prompt_injection_agent,
        app_name=app_name,
        session_service=session_service
    )

    # Send request to prompt attack agent
    print("Sending prompt to generate prompt injection attack...")
    user_input = """
        Please generate me 10 different prompt injection attacks.
        """
    content = types.Content(role="user", parts=[types.Part(text=user_input)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print("✅ Final response of prompt_injection_agent received.")
                print(f"prompt_injection_agent response: {response_text}")
                break
            else:
                print("⚠️ Final response of prompt_injection_agent was empty.")


async def call_prompt_leaking_agent():
    """Run prompt_leaking_agent agent"""

    # Set up session service and runner
    user_id = "user_1"
    session_id = "session_generate_001"
    app_name = "generate_app"
    session_service = InMemorySessionService()

    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

    runner = Runner(
        agent=prompt_leaking_agent,
        app_name=app_name,
        session_service=session_service
    )

    # Send request to prompt attack agent
    print("Sending prompt to generate 10 different prompt leaking attacks...")
    user_input = """
        Please generate me 10 different prompt leaking attacks.
        """
    content = types.Content(role="user", parts=[types.Part(text=user_input)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print("✅ Final response of prompt_leaking_agent received.")
                print(f"prompt_leaking_agent response: {response_text}")
                break
            else:
                print("⚠️ Final response of prompt_leaking_agent was empty.")


async def call_jailbreaking_agent():
    """Run jailbreaking_agent agent"""

    # Set up session service and runner
    user_id = "user_1"
    session_id = "session_generate_001"
    app_name = "generate_app"
    session_service = InMemorySessionService()

    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

    runner = Runner(
        agent=jailbreaking_agent,
        app_name=app_name,
        session_service=session_service
    )

    # Send request to prompt attack agent
    print("Sending prompt to generate 10 different jailbreaking attacks...")
    user_input = """
        Please generate me 10 different jailbreaking attacks.
        """
    content = types.Content(role="user", parts=[types.Part(text=user_input)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print("✅ Final response of jailbreaking_agent received.")
                print(f"jailbreaking_agent response: {response_text}")
                break
            else:
                print("⚠️ Final response of jailbreaking_agent was empty.")


if __name__ == "__main__":
    # print("Testing prompt injection attacks")
    # asyncio.run(call_prompt_injection_agent())
    # print("Finished testing prompt injection attacks")

    # print("Testing prompt leaking attacks")
    # asyncio.run(call_prompt_leaking_agent())
    # print("Finished testing prompt leaking attacks")

    print("Testing jailbreaking attacks")
    asyncio.run(call_jailbreaking_agent())
    print("Finished testing jailbreaking attacks")
