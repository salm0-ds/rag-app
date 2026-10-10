from openai import OpenAI
from pydantic import BaseModel, Field
import pandas as pd

import os

# api_key  = os.environ["OPENAI_API_KEY"]
api_key = "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"
# instructions  = os.environ["GEN_QUERY_INSTRCUTIONS"]
# input_payload  = os.environ["INPUT"]
# query_amount = os.environ["RANGE"]

# generate queries
# use small set of human queries
# output is strucutured

start = 0

class UserQuery(BaseModel):
    user_query: str = Field(description="A single user query string. MUST be between 20 and 75 characters long.",
                            min_length=20,
                            max_length=75
                            )

client = OpenAI(api_key=api_key)

instructions = (
    "You are an AI benchmark engineer specializing in Retrieval-Augmented Generation (RAG) systems. "
    "Your task is to generate realistic, challenging user queries designed to test dense vector retrieval, "
    "keyword matching, and semantic search over a knowledge base. "
    "Avoid generic questions. Make the queries sound natural, like a real user seeking information."
)

input_payload = (
    "Generate a complex, multi-hop test query"
    "The query should test whether the system can retrieve documents explaining why combining dense and sparse search is necessary."
)

def generate_query() -> str:
    response = client.responses.parse(
        model="gpt-6-luna",
        text_format=UserQuery,
        instructions=instructions,
        input=input_payload
    )
    return response

csv_filename = "test_dataset3.csv"
rows= []
while start < 5:
    gen_query = generate_query()
    data: UserQuery = gen_query.output_parsed
    string = data.user_query
    rows.append(string)
    start += 1

df1 = pd.DataFrame({"query":rows})
file_path = os.makedirs("backend/evals/datasets", exist_ok=True) 
df1.to_csv("backend/evals/datasets/queries.csv", index=False)