from openai import OpenAI
from pydantic import BaseModel, Field
from config import settings
import pandas as pd
import os

api_key  = settings.OPENAI_API_KEY
instructions  = settings.GEN_QUERY_INSTRCUTIONS
input_payload  = settings.QUERY_GEN_INPUT
count = settings.GEN_QUERY_COUNT
model = settings.GEN_QUERY_MODEL

class UserQuery(BaseModel):
    user_query: str = Field(description="A single user query string. MUST be between 20 and 75 characters long.",
                            min_length=20,
                            max_length=75
                            )
    reference: str = Field(description="generate any reference to the query",
                            min_length=20,
                            max_length=75
                            )

client = OpenAI(api_key=api_key, max_retries=3)

def generate_query() -> str:
    response = client.responses.parse(
        model=model,
        text_format=UserQuery,
        instructions=instructions,
        input=input_payload
    )

    parsed_data = response.output[1].content[0].parsed
    return {
        "user_query": parsed_data.user_query,
        "reference": parsed_data.reference
        }

def create_data(count):
  rows = []

  # 1. Collect all generated queries in a loop
  for i in range(count):
    output = generate_query()
    rows.append(
        {"user_query": output["user_query"], "reference": output["reference"]}
    )

  # 2. Convert the full list of rows into a single DataFrame
  df1 = pd.DataFrame(rows)

  # 3. Create the directory safely
  dir_path = "backend/evals/datasets"
  os.makedirs(dir_path, exist_ok=True)

  # 4. Define the proper file path string and save once
  file_path = os.path.join(dir_path, "queries.csv")
  df1.to_csv(file_path, index=False)

  print(
      f"Successfully generated {count} queries and saved to {file_path}!"
  )  #
  return True

create_data(count)

def create_dataset(csv_filename: str = "test_data_main.csv") -> list:

    filename = csv_filename
    gen_query = generate_query()
    data: UserQuery = gen_query.output_parsed
    string = data.user_query

    return
