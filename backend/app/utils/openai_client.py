import openai
from app.config import settings
from typing import List, Dict, Any

# Configure OpenAI client with API key from settings
openai.api_key = settings.OPENAI_API_KEY


async def generate_chat_completion(
    messages: List[Dict[str, str]],
    model: str = settings.OPENAI_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> Dict[str, Any]:
    """
    Generate a chat completion using OpenAI API.
    
    Args:
        messages: List of message objects with role and content
        model: OpenAI model to use
        temperature: Controls randomness (0-1)
        max_tokens: Maximum tokens to generate
        
    Returns:
        Complete response from OpenAI API
    """
    try:
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response
    except Exception as e:
        # Log the error and raise it for the caller to handle
        print(f"OpenAI API error: {str(e)}")
        raise 