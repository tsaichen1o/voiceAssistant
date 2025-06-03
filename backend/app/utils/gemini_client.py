import google.generativeai as genai
from app.config import settings
from typing import List, Dict, Any

# Configure Gemini client with API key from settings
genai.configure(api_key=settings.GEMINI_API_KEY)


async def generate_chat_completion(
    messages: List[Dict[str, str]],
    model: str = settings.GEMINI_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> Dict[str, Any]:
    """
    Generate a chat completion using Google Gemini API.
    
    Args:
        messages: List of message objects with role and content
        model: Gemini model to use
        temperature: Controls randomness (0-1)
        max_tokens: Maximum tokens to generate
        
    Returns:
        Complete response from Gemini API
    """
    try:
        # Initialize the model
        gemini_model = genai.GenerativeModel(model)
        
        # Convert messages to Gemini format
        # Gemini expects a conversation format, we'll concatenate user messages
        conversation_text = ""
        for message in messages:
            if message["role"] == "user":
                conversation_text += f"User: {message['content']}\n"
            elif message["role"] == "assistant":
                conversation_text += f"Assistant: {message['content']}\n"
            elif message["role"] == "system":
                conversation_text = f"System: {message['content']}\n" + conversation_text
        
        # Generate response
        response = gemini_model.generate_content(
            conversation_text,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        # Format response to match OpenAI structure
        formatted_response = {
            "choices": [
                {
                    "message": {
                        "content": response.text,
                        "role": "assistant"
                    }
                }
            ],
            "model": model,
            "usage": {
                "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0,
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            }
        }
        
        return formatted_response
    except Exception as e:
        # Log the error and raise it for the caller to handle
        print(f"Gemini API error: {str(e)}")
        raise 