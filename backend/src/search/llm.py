import os
import logging

from typing import Optional
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

system_context = os.getenv("SYSTEM_CONTEXT")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

model = os.getenv("LLM_MODEL")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")


try:
    client = OpenAI(api_key=api_key,
                    max_retries=3)
except Exception as e:
    logger.critical(f"Failed to initialize OpenAI client: {e}")
    raise ValueError("OpenAI client initialization failed") from e

def generate_llm_response(user_message: str,
                          context: Optional[str] = None,
                          chat_history: Optional[list[str]] = None) -> str:
    
    if not user_message or user_message is None:
        return "User message has not been sent"

    response = client.responses.create(
        input=f"""
        Answer the users query, analyse the context and previous chat history if there is any.
        User query:{user_message}
        Context provided: {context}
        Chat history: {chat_history}
        """,
        instructions=system_context,
        model=model
        )
  
    return response.output_text


