"""This is for calling the Email Agent, which is responsible for sending email
to human staff when the Base Agent encounters the question that it cannot answer.

Source: https://google.github.io/adk-docs/tutorials/agent-team/
"""

import asyncio
import os

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.services.email_agent import email_agent
from app.config import settings

os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY


class EmailAgent:
    """A class for managing conversation between email agent and user"""
    def __init__(self):
        """Initialize the class"""
        self.user_id = "user_1"
        self.session_id = "session_001"
        self.runner = None

    async def initialize_runner(self):
        """Initialize the session and the runner. This function should only be
        called one for each chat session, to keep chat history saved."""
        # Create a new session service to store state
        session_service = InMemorySessionService()
        # Create a new session
        app_name = "email_app"
        session = await session_service.create_session(
            app_name=app_name,
            user_id=self.user_id,
            session_id=self.session_id,
        )
        self.runner = Runner(
            agent=email_agent, # The agent we want to run
            app_name=app_name,   # Associates runs with our app
            session_service=session_service # Uses our session manager
        )
        return self.runner


    async def call_agent_async(self, user_input: str):
        """Sends a query to the agent and return the final response.
        Args:
            user_input (str): user input
        """
        print(f"\n>>> User Question: {user_input}")

        # Prepare the user's message in ADK format
        content = types.Content(role='user', parts=[types.Part(text=user_input)])

        final_response_text = "Agent did not produce a final response." # Default

        # We iterate through events to find the final answer.
        async for event in self.runner.run_async(user_id=self.user_id, session_id=self.session_id, new_message=content):
            # See all events during execution
            print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

            # Key Concept: is_final_response() marks the concluding message for the turn.
            if event.is_final_response():
                if event.content and event.content.parts:
                    # Assuming text response in the first part
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                break # Stop processing events once the final response is found

        print(f"<<< Agent Response: {final_response_text}")
        return final_response_text

# -------- For testing this file independently ------------------------------
async def main():
    """Stimulate a conversation to test the functionality"""
    email_class = EmailAgent()
    runner = await email_class.initialize_runner()
    print("HELLO, WELCOME TO THE EMAIL AGENT")
    user_question = ""
    while user_question != "q":
        user_question = input("How can we help you: ")
        print(f"User: {user_question}")
        agent_response = await email_class.call_agent_async(user_question)
        print(f"Agent: {agent_response}")


if __name__ == "__main__":
    asyncio.run(main())
