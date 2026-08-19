from llama_index.readers.s3 import S3Reader
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import StorageContext, VectorStoreIndex, Document
from llama_parse import LlamaParse

from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

import os
"""
# 1. Load documents from S3
s3_reader = S3Reader(
    bucket="ragapp-userfile-s3bucket-214269449513-eu-west-2-an",
    key="test1text.txt",  # optional, for subfolders
    aws_access_id="AKIATDY3UKUU2VG5GQF6",
    aws_access_secret="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",
    region_name="eu-west-2"
)
documents = s3_reader.load_data()


# 2. Set up Postgres vector store
vector_store = PGVectorStore.from_params(
    database="myragdb",
    host="localhost",
    user="postgres",
    password="Aalam357!POSTGRES",
    port=5432,
    table_name="vector_embeds",
    embed_dim=1536,
    hybrid_search=True,
    text_search_config='english'
)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 3. Build the index (embeddings are created automatically)
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context, show_progress=True
)

parser = LlamaParse()
"""

def rag_pipeline(filename):
    s3_reader = S3Reader(
    bucket="ragapp-userfile-s3bucket-214269449513-eu-west-2-an",
    key=filename,  # optional, for subfolders
    aws_access_id="AKIATDY3UKUU2VG5GQF6",
    aws_access_secret="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",
    region_name="eu-west-2")

    documents = s3_reader.load_data()

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True            # Disable OCR to skip heavy vision processing
    pipeline_options.do_table_structure = False   # Disable heavy table extraction models
    
    # 3. Pass the backend directly into PdfFormatOption
    converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options,
            backend=PyPdfiumDocumentBackend
            )
        }
    )

    # 4. Execute the conversion
    result = converter.convert(documents)
    markdown_output = result.document.export_to_markdown()

    vector_store = PGVectorStore.from_params(
    database="myragdb",
    host="localhost",
    user="postgres",
    password="Aalam357!POSTGRES",
    port=5432,
    table_name="vector_embeds",
    embed_dim=1536,
    hybrid_search=True,
    text_search_config='english')

    storage_context = StorageContext.from_defaults(vector_store=vector_store, embed_model='local')


    index = VectorStoreIndex.from_documents(
    markdown_output, storage_context=storage_context, show_progress=True)

    # if file in s3 return true

    return True

from io import BytesIO

import boto3
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.postgres import PGVectorStore


from llama_index.embeddings.openai import OpenAIEmbedding



def rag_pipeline2(filename):
    # 1. Download the raw file from S3 straight into memory
    aws = boto3.Session(
    aws_access_key_id="AKIATDY3UKUU2VG5GQF6",
    aws_secret_access_key="w7P2m7ZMBVK2CKMEjU71U8uxWTw5b1RkXjc11DkT",
    region_name="eu-west-2")

    s3 = aws.client("s3")
      # use your existing credentials setup

    buffer = BytesIO()
    s3.download_fileobj(
        "ragapp-userfile-s3bucket-214269449513-eu-west-2-an",
        filename,
        buffer
    )
    buffer.seek(0)  # rewind after writing, so docling reads from the start

    # 2. Convert PDF -> markdown with docling, reading from the in-memory stream
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )

    embed_model = OpenAIEmbedding(
    api_key="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",  # ideally from os.getenv("OPENAI_API_KEY")
    model="text-embedding-3-small")   # matches your embed_dim=1536 in PGVectorStore

    source = DocumentStream(name=filename, stream=buffer)
    result = converter.convert(source)  # pass the stream, not a path or llama-index Documents
    markdown_output = result.document.export_to_markdown()

    # 3. Wrap the markdown string back into a llama-index Document
    documents = [Document(text=markdown_output, metadata={"file_name": filename})]

    # 4. Index as before
    vector_store = PGVectorStore.from_params(
        database="myragdb",
        host="localhost",
        user="postgres",
        password="Aalam357!POSTGRES",
        port=5432,
        table_name="vector_embeds",
        embed_dim=1536,
        hybrid_search=True,
        text_search_config="english"
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=embed_model,
    show_progress=True)

    return True