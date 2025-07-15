import requests
# For randomly selecting programs
import random
import json
import os
from typing import Dict
from app.tests.tum_data_retriever import WebScraper
from google.adk.agents import Agent
from app.config import settings
from app.services.chat_service import stream_chat_response
import asyncio

# URL contains all TUM programs
MAIN_URL = "https://www.tum.de/en/studies/degree-programs"
# Path to the json file storing the TUM programs that we haven't used in test
UPDATED_TUM_PROGRAMS_DICT_PATH = r"./app/tests/test_results/tum_programs_to_select.json"


def load_remaining_programs() -> Dict[str, Dict]:
    """Loading the TUM programs that are not yet discovered."""
    try:
        with open(UPDATED_TUM_PROGRAMS_DICT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        web_scraper = WebScraper(main_url=MAIN_URL)
        program_dict = web_scraper.get_tum_programs_dict()
        return program_dict


def save_remaining_programs(programs: Dict[str, Dict]):
    """Update the TUM programs not discovered dict by deleting mewly discovered program"""
    with open(UPDATED_TUM_PROGRAMS_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(programs, f, ensure_ascii=False, indent=2)


def randomly_select_a_program() -> dict:
    """Randomly selected a program that has not been selected yet and get all
    its available information."""
    tum_programs_dict = load_remaining_programs()
    print(f"The number of undiscovered TUM programs: {len(tum_programs_dict)}")
    if not tum_programs_dict:
        return {
            "status": "done",
            "report": "All programs have already been selected."
        }
    
    program_name = random.choice(list(tum_programs_dict.keys()))
    program_data = tum_programs_dict.pop(program_name)
    program_description = program_data.get("program description", "")

    save_remaining_programs(tum_programs_dict)

    if program_description:
        return {
            "status": "success",
            "report": (f"The information about the program {program_name} is: {program_description}")
        }
    else:
        return {
            "status": "error",
            "report": f"No information found for the program {program_name}"
        }


async def ask_llm_chatbot(prompt: str) -> dict:
    """Ask question to LLM chatbot and get the response
    Args:
        prompt (str): the prompt (question) about TUM program that you wnat to ask chatbot
    """
    print(f"Question to LLM: {prompt}")
    messages = [{"role": "user", "content": prompt}]
    full_response = ""
    async for chunk in stream_chat_response(messages, "abc"):
        if isinstance(chunk, bytes):
            full_response += chunk.decode('utf-8')
        for line in chunk.strip().splitlines():
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data in ("[done]", "[error]"):
                continue
            try:
                payload = json.loads(data)
                if payload.get("type") == "content":
                    full_response += payload.get("content", "")
            except json.JSONDecodeError:
                continue
    print(f"LLM chatbot response: {full_response}")
    # Store the chat history in a .jsonl file
    # Path to the file that stores the chat history
    chat_history_path = r"./app/tests/test_results/chat_history.jsonl"
    # Ensure the directory exists
    os.makedirs(os.path.dirname(chat_history_path), exist_ok=True)
    try:
        with open(chat_history_path, "a", encoding="utf-8") as file:
            json.dump({
                "test_agent question": prompt,
                "chatbot response": full_response
            }, file, ensure_ascii=False)
            file.write("\n")
    except Exception as e:
        print(f"[Logging Error] Could not write to log file: {e}")
    return {
        "status": "success",
        "report": f"LLM chatbot response: {full_response}"
    }


def save_test_report(test_report: dict):
    """Append test_report to a JSONL file as a separate line.
    Args:
        test_report (dict): a python dict (or json) in the format {"question": [str], "correct answer": [str], "llm answer": [str], "assessment": [bool]}
    """
    test_report_path = r"./app/tests/test_results/test_reports.jsonl"

    try:
        # Try to convert from string if not a dict
        if isinstance(test_report, str):
            try:
                test_report = json.loads(test_report)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to save report: {e}")
                print(f"test_report that attempted to save: {test_report}")
                return {
                    "status": "error",
                    "report": f"Provided string could not be parsed as JSON: {e}"
                }

        # Final check: must be a dict
        if not isinstance(test_report, dict):
            print("❌ Failed to save report")
            print(f"test_report that attempted to save: {test_report}")
            return {
                "status": "error",
                "report": f"test_report must be a dict, got {type(test_report)} instead"
            }
        # Validate required keys
        required_keys = {"question", "correct answer", "llm answer", "assessment"}
        missing = required_keys - set(test_report.keys())
        if missing:
            return {
                "status": "error",
                "report": f"Missing keys in test_report: {missing}"
            }

        # Save single entry to JSONL
        with open(test_report_path, "a", encoding="utf-8") as f:
            json.dump(test_report, f, ensure_ascii=False)
            f.write("\n")

        print(f"✅ Appended test report for: {test_report['question']}")
        return {
            "status": "success",
            "report": f"Appended test result for: {test_report['question']}"
        }

    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        print(f"test_report that attempted to save: {test_report}")
        return {
            "status": "error",
            "report": f"Failed to save test report. Caught this error: {e}"
        }


test_chatbot_agent = Agent(
    name="test_chatbot_agent",
    model=settings.GEMINI_MODEL,
    description=(
        "Agent to generate questions about TUM programs"
    ),
    instruction=(
        """You are a helpful agent who helps in testing the accuracy of an LLM-based
        chatbot that answers questions about Technical University of Munich (TUM)
        programs. Your task is to:
        1. Randomly select 10 TUM programs and for each program, generate a 
        question that user might ask the chatbot. The question
        should be based on the program's information and should be clear enough
        so that there is only one correct answer. For example,
        Question: What is the program Aerospace - Bachelor of Science (B.Sc.)'s standard 
        duration of studies?
        Correct answer: 6 semesters.
        Or
        Question: What is the Required Language Proficiency for the program AgriFood 
        Economics, Policy and Regulation - Master of Science (M.Sc.)?
        Correct answer: English
        2. Ask the question to LLM chatbot. If the chatbot requires additional
        information to reduce the ambigious of the question or confusion, you 
        can provide it. However, you must not provide the answer
        directly to the chatbot, because you are testing it.
        3. Assess whether the LLM's answer is correct or not. You should continue
        the conversation, clarify the question if needed, until you get the
        firm answer from the chatbot.
        4. For each of the question, fill in this jsonl template:
        JSON:
        test_report = {
            "question": [str, a question that you want to ask chatbot],
            "correct answer": [str, the correct answer to the question],
            "llm answer": [str, the LLM response that contains the answer],
            "assessment": [bool, whether the LLM's answer is correct or not]
        }
        5. For each of the question, save the test_report json to the .jsonl file
        by calling save_test_report(test_report), where test_report is the json
        you generated in previous step for each question.
        Try to follow exactly the json format mentioned in step 4 when adding
        parameter test_report to save_test_report(test_report) tool so that the
        tool can save to the file successfully.
        NOTE that you should use ONLY the available information provided by the
        randomly_select_a_program tool.
        NOTE generate the prompts to the chatbot in a way that chat history is
        not required for the chatbot to answer the question.
        """
    ),
    tools=[randomly_select_a_program, ask_llm_chatbot, save_test_report],
)
async def main():
    prompt = input("User input: ")
    result = await ask_llm_chatbot(prompt)
    print(f"LLM response: {result}")

if __name__ == "__main__":
    asyncio.run(main())

