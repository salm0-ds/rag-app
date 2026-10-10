import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd


# load backend/.env explicitly

from backend.src.search.rag_llm_decider import search_decider

query_amount = 5

df = pd.read_csv("backend/evals/datasets/queries.csv")



rows = []

for i in range(query_amount):
    query = df.loc[i, "query"]
    output = search_decider(query)
    rows.append({
        "query": query,
        "output": output.result
    })

df1 = pd.DataFrame(rows)

print(df1)
df1.to_csv("backend/evals/datasets/output.csv", index=False)

