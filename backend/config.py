import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEN_QUERY_INSTRCUTIONS = (
        "You are an AI benchmark engineer specializing in Retrieval-Augmented Generation (RAG) systems. "
        "Generate realistic user queries that can be answered from the given document text. "
        "Make them sound natural, like a real user seeking information."
    )
    QUERY_GEN_INPUT = (
        "You are an AI benchmark engineer specializing in Retrieval-Augmented Generation (RAG) systems. "
        "Generate realistic user queries that can be answered from the given document text. "
        "Make them sound natural, like a real user seeking information."
    )
    GEN_QUERY_COUNT = 4
    GEN_QUERY_MODEL = "gpt-6-luna"

    INPUT_EVAL_DATA_ADD = "backend/evals/datasets/queries.csv"
    OUTPUT_EVAL_DATA_ADD = "backend/evals/datasets/output.csv"
    DATASET_PATH = "backend/evals/datasets/"

    GEN_QUERY_MODEL = "gpt-6-luna"
    EVAL_MODEL = "gpt-6-luna"
    EMBED_PROVIDER = "openai"
    EVAL_EMBED_MODEL = "text-embedding-3-small"


# 1. Initialize the settings object first!
settings = Settings()