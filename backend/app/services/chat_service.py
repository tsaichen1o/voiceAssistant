# -*- coding: utf-8 -*-

from typing import Dict, Any, Optional, AsyncGenerator
from app.models.schemas import Message, ChatRequest, ChatResponse, RAGRequest, Usage
from app.config import settings
import google.generativeai as genai
from app.services.session_service import (
    create_session,
    get_session,
    update_session,
    redis_client,
)
from datetime import datetime, timezone
import uuid
import asyncio
import json
from fastapi import HTTPException
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
import google.generativeai as genai
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

# Source: https://cloud.google.com/generative-ai-app-builder/docs/preview-search-results?hl=zh-tw#genappbuilder_search_lite-python


# Configure Gemini client
genai.configure(api_key=settings.GEMINI_API_KEY)


# TODO: Handle stream error
# TODO: Handle language
# TODO: Handle multiple turn chatting
async def stream_chat_response(
    messages: list, stream_id: str
) -> AsyncGenerator[str, None]:
    try:
        if not messages:
            yield "data: [error] No message provided.\n\n"
            return

        user_question = messages[-1].get("content", "")
        if not user_question.strip():
            yield "data: [error] Empty message content.\n\n"
            return

        # ===== 1. Vertex AI Search, get summary/citations =====
        project_id = settings.VERTEX_AI_SEARCH_PROJECT_ID
        location = settings.VERTEX_AI_SEARCH_LOCATION
        engine_id = settings.VERTEX_AI_SEARCH_ENGINE_ID

        client_options = (
            ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
            if location != "global"
            else None
        )

        client = discoveryengine.SearchServiceClient(client_options=client_options)
        serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"
        print("SEARCH SERVING CONFIG:", serving_config)

        content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,
                include_citations=True,
                ignore_adversarial_query=True,
                ignore_non_summary_seeking_query=True,
                model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                    preamble="Please help me answer TUM application questions based on the following content."
                ),
                model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                    version="stable"
                ),
            ),
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True
            ),
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=user_question,
            page_size=10,
            content_search_spec=content_search_spec,
            # query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            #     condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO
            # ),
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
            ),
        )

        search_response = client.search(request)
        summary_text = ""
        citations = []

        if hasattr(search_response, "summary") and search_response.summary:
            summary_text = search_response.summary.summary_text
            if hasattr(search_response.summary, "citation_metadata"):
                # citation_metadata is a repeated field
                citations = [
                    {"title": c.title, "uri": c.uri}
                    for c in getattr(
                        search_response.summary.citation_metadata, "citations", []
                    )
                ]

        # ===== 2. Prepare prompt for Gemini =====
        system_prompt = (
            "You are a RAG chatbot who provides professional advice (in Markdown format) to applicants interested in applying to TUM programs.\n"
            "\n"
            "Always answer based only on the official knowledge found in the following Context. "
            "If you cannot find the answer from the Context, simply state that the information is not available in your data. Do not make up an answer.\n"
            "If the user's question is ambiguous, ask follow-up questions to clarify what they need.\n"
            "\n"
            "Special rule regarding tuition fees: \n"
            "- If a program explicitly mentions tuition fees for international students, treat it as not free for international students.\n"
            "- If the context does not mention tuition fees, treat the program as having no tuition fee.\n"
            "\n"
            "Format your response in Markdown. Each answer must include:\n"
            "- **Answer** (the direct answer)\n"
            "- **Explanation** (further details or reasoning)\n"
            "- **Program URLs** (if available from the context)\n"
            "\n"
            "Cite sources if relevant. Be professional and clear."
        )
        # system_prompt = (
            # "You are a professional academic advisor for prospective TUM students. Your main language is English. Your responses must be structured, clear, and easy to read.\n"
            # "\n"
            # "--- CORE INSTRUCTIONS ---\n"
            # "1.  **Answer from Context Only**: Always answer based only on the official knowledge found in the following Context. \n"
            # "2.  **If No Answer**: If you cannot find the answer from the Context, simply state that the information is not available in your data ('Based on my current data, I cannot find any specific information about ...'). Do not make up an answer.\n"
            # "3.  **Clarify Ambiguity**: If the user's question is ambiguous, ask follow-up questions to clarify what they need.\n"
            # "4.  **Tuition Fee Rule**: If a program explicitly mentions tuition fees for international students, treat it as not free. If the context does not mention tuition fees, treat the program as having no tuition fee for EU students, but mention that fees may apply to non-EU students.\n"
            # "\n"
            # "--- MARKDOWN FORMATTING GUIDE ---\n"
            # "You **MUST** format your entire response in Markdown using the following structure and rules:\n"
            # "\n"
            # "1.  **Overall Structure**:\n"
            # "    - Start with a main heading `##` for the direct answer.\n"
            # "    - Follow with a `### Details` section for further details.\n"
            # "    - If applicable, add a `### Related Links` section at the end for URLs.\n"
            # "\n"
            # "2.  **Emphasis**:\n"
            # "    - Use **bold text** (`**...**`) for key terms, program names, deadlines, and important requirements (e.g., **TUM School of Management**, **15th March**, **TOEFL score**).\n"
            # "    - Use *italic text* (`*...*`) for subtle emphasis or notes.\n"
            # "\n"
            # "3.  **Lists**:\n"
            # "    - For multiple items, requirements, or features, use a bulleted list (`*` or `-`).\n"
            # "    - For step-by-step instructions (like an application process), use a numbered list (`1.`, `2.`, `3.`).\n"
            # "\n"
            # "4.  **Tables**: \n"
            # "    - When comparing programs or listing data with multiple attributes (e.g., Program Name, ECTS, Duration), **ALWAYS** format the information as a Markdown table for clarity. Example:\n"
            # "      | Item | Content |\n"
            # "      | :--- | :--- |\n"
            # "      | Degree | Master of Science |\n"
            # "      | ECTS | 120 ECTS |\n"
            # "\n"
            # "5.  **Quoting**: \n"
            # "    - When directly quoting a key sentence from the provided Context, use a blockquote (`>`) to clearly indicate it's an official statement.\n"
            # "\n"
            # "6.  **Links**:\n"
            # "    - Format all URLs as clean, clickable Markdown links. Example: `[TUM Website](https://www.tum.de)`.\n"
            # "\n"
            # "Be professional, clear, and respond in English primarily, but also in Chinese if the user's question is in Chinese and specify Simplified Chinese and Traditional Chinese. Please use the user's language to respond."
        # )

        # TODO: add chat history
        if summary_text:
            prompt_for_gemini = (
                f"{system_prompt}\n\n"
                f"--- Context ---\n"
                f"{summary_text}\n"
                f"--- END OF CONTEXT ---\n"
                f"\n"
                # f"Chat history: {chat_history}\n"
                f"Latest user question: {user_question}"
            )
        else:
            prompt_for_gemini = (
                f"{system_prompt}\n\n"
                "No official information matching the user's question was found in the knowledge base.\n"
                "Politely suggest the user to rephrase or ask a different question."
                # f"\n\nChat history: {chat_history}\n"
                f"Latest user question: {user_question}"
            )

        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response_stream = model.generate_content(prompt_for_gemini, stream=True)

        # ===== 3. stream Gemini result =====
        for chunk in response_stream:
            if chunk.text:
                data_payload = {"content": chunk.text}
                yield f"data: {json.dumps(data_payload)}\n\n"
                await asyncio.sleep(0.05)
        # add citations at the end
        yield f"data: {json.dumps({'content': '', 'citations': citations})}\n\n"

    except Exception as e:
        print(f"Error during stream generation: {e}")
        yield f"data: [error] An error occurred while generating the response.\n\n"
    finally:
        redis_client.delete(f"stream_request:{stream_id}")
        yield "data: [done]\n\n"


async def stream_chat_response_basic(
    messages: list, stream_id: str
) -> AsyncGenerator[str, None]:
    """
    An async generator that streams responses from the Gemini model.
    Basic version without RAG for testing.
    """
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        system_prompt = """
        You are a helpful assistant. All your responses must be formatted using Markdown.
        - Use headings (##, ###) for main topics.
        - Use bullet points (*) or numbered lists (1.) for lists.
        - Use bold (**) and italics (*) for emphasis.
        - Use code blocks (```) for code snippets.
        - Respond in the user's language.
        - No redundant gap between paragraphs.
        """

        if not messages:
            yield "data: [error] No message provided.\n\n"
            return

        last_user_message = messages[-1]
        user_question = last_user_message.get("content", "")

        if not user_question.strip():
            yield "data: [error] Empty message content.\n\n"
            return

        prompt_for_model = f"{system_prompt}\n\n---\n\nUSER QUESTION: {user_question}"

        response_stream = model.generate_content(
            prompt_for_model,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=800,
            ),
        )

        for chunk in response_stream:
            if chunk.text:
                data_payload = {"content": chunk.text}
                yield f"data: {json.dumps(data_payload)}\n\n"
                await asyncio.sleep(0.02)

    except Exception as e:
        print(f"Error during stream generation: {e}")
        error_payload = {
            "content": f"[error] An error occurred while generating the response: {str(e)}"
        }
        yield f"data: {json.dumps(error_payload)}\n\n"
        yield "data: [done]\n\n"

    finally:
        redis_client.delete(f"stream_request:{stream_id}")
        print(f"Cleaned up Redis key for stream: {stream_id}")
        yield "data: [done]\n\n"


async def get_chat_response(
    request: ChatRequest, user_info: Optional[Dict[str, Any]] = None
) -> ChatResponse:
    """
    Process a chat request and return a response from the Gemini model.

    Args:
        request: The chat request containing messages and parameters
        user_info: User authentication information (optional for backward compatibility)

    Returns:
        ChatResponse: The model's response
    """
    session_id = request.session_id
    user_id = user_info.get("user_id") if user_info else None

    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    if not session_id:
        if user_info and user_info.get("auth_type") == "supabase":
            session_id = create_session(user_id=user_id)
        else:
            session_id = create_session()
    else:
        if user_info and user_info.get("auth_type") == "supabase":
            session = get_session(session_id, user_id=user_id)
        else:
            session = get_session(session_id)

        if not session:
            if user_info and user_info.get("auth_type") == "supabase":
                session_id = create_session(user_id=user_id)
            else:
                session_id = create_session()

    # Initialize Gemini model
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    # Convert messages to Gemini format
    conversation_text = ""
    for message in request.messages:
        if message.role == "user":
            conversation_text += f"User: {message.content}\n"
        elif message.role == "assistant":
            conversation_text += f"Assistant: {message.content}\n"
        elif message.role == "system":
            conversation_text = f"System: {message.content}\n" + conversation_text

    # Generate response with Gemini
    response = model.generate_content(
        conversation_text,
        generation_config=genai.types.GenerationConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        ),
    )

    # Extract the response message
    assistant_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=response.text,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # Update session with message history - include user context
    messages = [m.model_dump() for m in request.messages]
    messages.append(assistant_message.model_dump())

    if user_info and user_info.get("auth_type") == "supabase":
        update_session(session_id, messages, user_id=user_id)
    else:
        update_session(session_id, messages)

    # Convert usage to our Usage model if available
    usage_data = None
    if response.usage_metadata:
        usage_data = Usage(
            completion_tokens=response.usage_metadata.candidates_token_count,
            prompt_tokens=response.usage_metadata.prompt_token_count,
            total_tokens=response.usage_metadata.total_token_count,
            completion_tokens_details=None,
            prompt_tokens_details=None,
        )

    # Return the response
    return ChatResponse(
        message=assistant_message,
        model=settings.GEMINI_MODEL,
        usage=usage_data,
        session_id=session_id,
    )


# Placeholder for future RAG-enhanced chat
async def get_rag_chat_response(request: RAGRequest) -> ChatResponse:
    """
    Process a RAG-enhanced chat request.
    This is a placeholder for future RAG implementation.

    Args:
        request: The RAG request containing messages, query, and parameters

    Returns:
        ChatResponse: The model's response
    """
    # For now, just return a message that this feature is coming soon
    # TODO: add system prompt
    session_id = request.session_id or "rag_placeholder_session"
    assistant_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content="RAG-enhanced chat is coming soon. This feature will allow the model to reference external documents.",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    return ChatResponse(
        message=assistant_message,
        model="placeholder",
        usage=None,
        session_id=session_id,
    )


# Placeholder for future voice-related functionality
async def transcribe_audio():
    """Placeholder for future voice transcription functionality."""
    pass


async def get_session_history(session_id: str, user_id: Optional[str] = None):
    """
    Retrieve chat history for a session.

    Args:
        session_id: The session ID to retrieve history for
        user_id: Optional user ID for access control

    Returns:
        dict: The session data including message history
        None: If session not found or access denied
    """
    if user_id:
        return get_session(session_id, user_id=user_id)
    else:
        return get_session(session_id)
