import cohere
import os

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.embeddings.openai import OpenAIEmbedding

api_key = os.getenv("OPENAI_API_KEY")
embedding_model = os.getenv("EMBED_MODEL")
cohere_api_key = os.getenv("COHERE_API_KEY")

host=os.getenv("HOST")
db_name=os.getenv("DB_NAME")
db_user=os.getenv("DB_USER")
db_password=os.getenv("DB_PASSWORD")
db_port=os.getenv("DB_PORT")
db_table_name=os.getenv("TABLE_NAME")
rerank_model=os.getenv("RERANK_MODEL")

co = cohere.ClientV2(api_key=cohere_api_key)
embed_model = OpenAIEmbedding(
    api_key=api_key,
    model=embedding_model) 

# connect to database using llamaindex


def rag_search(query: str, folder_id: str):
    
    vector_store = PGVectorStore.from_params( 
    hybrid_search=True,
    database=db_name,
    host=host,
    password=db_password,
    user=db_user,
    port=db_port,
    table_name=db_table_name,
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
        model=rerank_model,
        )

    top_chunks_after_rerank = [list[result.index] for result in response.results]

    context = [
    {"data": {"title": "chunk 0", "snippet": top_chunks_after_rerank[0]}},
    {"data": {"title": "chunk 1", "snippet": top_chunks_after_rerank[1]}},
    {"data": {"title": "chunk 2", "snippet": top_chunks_after_rerank[2]}},
    ]

    return context