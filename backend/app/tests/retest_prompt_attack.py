import json
import asyncio
from app.services.chat_service import stream_chat_response

async def redo_previous_attacks() -> list:
    """Return a list of previous prompts (attacks) and their responses"""
    file_path = r"./app/tests/test_results/attack_success_before.jsonl"
    result_path = r"./app/tests/test_results/attack_retry.jsonl"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                attack = json.loads(line)
                attack_prompt = attack.get("attack prompt", "")
                if attack_prompt:
                    response = await ask_llm_chatbot(attack_prompt)
                    if response:
                        result = {
                            "type of attack": attack.get("type of attack"),
                            "attack prompt": attack_prompt,
                            "chatbot response": response
                        }
                        # Save single entry to JSONL
                        with open(result_path, "a", encoding="utf-8") as f:
                            json.dump(result, f, ensure_ascii=False)
                            f.write("\n")
                        print(f"Update to file {result_path}")
                        continue
                    break
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")



async def ask_llm_chatbot(prompt: str) -> str:
    """Ask a question to the LLM chatbot and get the response.

    Args:
        prompt (str): The prompt (question) about the TUM program.

    Returns:
        str: The chatbot's full response (newlines removed).
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

    # Remove newline characters
    full_response = full_response.replace("\n", "")

    print(f"LLM chatbot response: {full_response}")

    # Store the chat history in a .jsonl file
    chat_history_path = r"./app/tests/test_results/promt_attack_chat_history_after.jsonl"
    try:
        with open(chat_history_path, "a", encoding="utf-8") as file:
            json.dump({
                "test_agent question": prompt,
                "chatbot response": full_response
            }, file, ensure_ascii=False)
            file.write("\n")
    except Exception as e:
        print(f"[Logging Error] Could not write to log file: {e}")

    return full_response

if __name__ == "__main__":
    asyncio.run(redo_previous_attacks())