import os
import logging

from dotenv import load_dotenv
from openai import OpenAI, UnprocessableEntityError, APIError, RateLimitError
from pydantic import BaseModel, Field
from typing import Literal, Optional

load_dotenv()
logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

model = os.getenv("SUM_MODEL")
if not model:
    raise ValueError("SUM_MODEL environment variable is required")

instructions = os.getenv("SUM_INSTRUCT")
if not instructions:
    raise ValueError("SUM_INSTRUCT environment variable is required")

dec_instruct = os.getenv("DEC_INSTRUCT")
if not dec_instruct:
    raise ValueError("DEC_INSTRUCT environment variable is required")

try:
    client = OpenAI(api_key=api_key,
                    max_retries=3)
except Exception as e:
    logger.critical(f"Failed to initialize OpenAI client: {e}")
    raise ValueError("OpenAI client initialization failed") from e

class DeciderOutput(BaseModel):
        result: Literal['rag_search', 'llm_answer'] = Field(description="Choose rag_search if the query explicitly or implicitly requires searching through company files, documents, or knowledgebases. Choose direct_llm for general conversations, small talk, or queries needing broad generic logic.")
        confidence: int = Field(
            description="Produce a confidence level percentage of your result",
            ge=0,
            le=100)
        
class prev_mes_sum(BaseModel):
      summary: str = Field(max_length=500)

def sum_prev_mes(rows: Optional[list[str]] = None) -> Optional[prev_mes_sum]:
    """
    Takes the chat histroy and generates a summary  
    """

    if not rows or rows is None:
         return None


    messages = [{"role":rows[i][1], "content":rows[i][2]} for i in range(len(rows))]

    try:
        response = client.responses.parse(
            model = model,
            instructions=instructions,
            input=messages,
            text_format=prev_mes_sum
            )
        return response.output_parsed
   
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        return None
    except UnprocessableEntityError as e:
        logger.error(f"Issue processing request: {e}")
        return None


def search_decider(query: str) -> DeciderOutput:
    """
    Takes the user query and decides whether a rag search would be neccessary  
    """

    if not query or query is None:
        return "User message has not been sent"

    try:
        response = client.responses.parse(
            model = model,
            instructions=dec_instruct,
            input=query,
            text_format=DeciderOutput
            )

        return response.output_parsed
    except RateLimitError as e:
        logger.warning(f"Rate limit hit: {e}")
        raise RateLimitError("I'm receiving too many requests right now. Please try again in a moment.")
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise APIError("There was a problem processing your request. Please try again.")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        raise Exception("An unexpected error occurred. Our team has been notified.")






    
    


