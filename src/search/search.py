# llamaindex
# open ai
# postgres
# cohere

import cohere

co = cohere.ClientV2(api_key="dXJ4Xc5xrc6egQnhLXO8w4L01iuprSsjrrTzQaZE") # Get your free API key: https://dashboard.cohere.com/api-keys


from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
"""
query = "what is this about"

# 1. Connect to the existing store
vector_store = PGVectorStore.from_params( # your existing Postgres connection parameters
    hybrid_search=True, # Enable this if you want to use Postgres text search + vectors
    database="myragdb",
    host="localhost",
    password="Aalam357!POSTGRES",
    user="postgres",
    port=5432,
    table_name="vector_embeds",
    embed_dim=1536,
    text_search_config="english"
)

# 2. Assign the store to a context
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 3. Load the index from the existing store (NO documents passed)
index = VectorStoreIndex.from_vector_store(
    vector_store, 
    storage_context=storage_context
)

retriever = index.as_retriever(vector_store_query_mode="hybrid", similarity_top_k=10)
results = retriever.retrieve(query)


list = []
for i in range(len(results)):
    list.append(results[i].node.text)



response = co.rerank(
    query=query,
    documents=list,
    top_n=3,
    model="rerank-english-v3.0",
)

# top_chunks_after_rerank = [result.document['text'] for result in response]

top_chunks_after_rerank = [list[result.index] for result in response.results]

# preamble containing instructions about the task and the desired style for the output.



# retrieved documents
documents = [
    {"data": {"title": "chunk 0", "snippet": top_chunks_after_rerank[0]}},
    {"data": {"title": "chunk 1", "snippet": top_chunks_after_rerank[1]}},
    {"data": {"title": "chunk 2", "snippet": top_chunks_after_rerank[2]}},
  ]

# get model response
response = co.chat(
  model="command-r-08-2024",
  messages=[{"role" : "system", "content" : preamble},
            {"role" : "user", "content" : query}],
  documents=documents,  
  temperature=0.3
)

print("Final answer:")
print(response.message.content[0].text)

"""

from llama_index.embeddings.openai import OpenAIEmbedding

embed_model = OpenAIEmbedding(
    api_key="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",  # ideally from os.getenv("OPENAI_API_KEY")
    model="text-embedding-3-small") 

def rag_search(query: str, folder_id: str):
    
    vector_store = PGVectorStore.from_params( 
    hybrid_search=True,
    database="myragdb",
    host="localhost",
    password="Aalam357!POSTGRES",
    user="postgres",
    port=5432,
    table_name="vector_embeds",
    embed_dim=1536,
    text_search_config="english",
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store, 
        storage_context=storage_context,
        embed_model=embed_model)
    filters = MetadataFilters(filters=[MetadataFilter(key="folder_id", value=folder_id)])
    retriever = index.as_retriever(vector_store_query_mode="hybrid", similarity_top_k=10, filter=filters)
    results = retriever.retrieve(query)

    list = []
    for i in range(len(results)):
        list.append(results[i].node.text)


    response = co.rerank(
        query=query,
        documents=list,
        top_n=3,
        model="rerank-english-v3.0",
        )

    top_chunks_after_rerank = [list[result.index] for result in response.results]

    context = [
    {"data": {"title": "chunk 0", "snippet": top_chunks_after_rerank[0]}},
    {"data": {"title": "chunk 1", "snippet": top_chunks_after_rerank[1]}},
    {"data": {"title": "chunk 2", "snippet": top_chunks_after_rerank[2]}},
    ]

    return context