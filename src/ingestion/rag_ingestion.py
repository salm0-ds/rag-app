from llama_index.readers.s3 import S3Reader
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import StorageContext, VectorStoreIndex, Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_parse import LlamaParse

from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

from io import BytesIO

import os
import boto3

aws_access_key=os.getenv("AWS_ACCESS_KEY")
aws_secret_access=os.getenv("AWS_SECRET_ACCESS")
region_name=os.getenv("REGION_NAME")
aws_bucket=os.getenv("AWS_BUCKET")
openai_api_key=os.getenv("OPENAI_API_KEY")
embed_model=os.getenv("EMBED_MODEL")

host=os.getenv("HOST")
db_name=os.getenv("DB_NAME")
db_user=os.getenv("DB_USER")
db_password=os.getenv("DB_PASSWORD")
db_port=os.getenv("DB_PORT")
db_table_name=os.getenv("TABLE_NAME")
rerank_model=os.getenv("RERANK_MODEL")

def rag_pipeline(filename):
    # 1. Download the raw file from S3 straight into memory
    aws = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access,
    region_name=region_name)

    s3 = aws.client("s3")
      # use your existing credentials setup

    buffer = BytesIO()
    s3.download_fileobj(
        aws_bucket,
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
    api_key=openai_api_key,  # ideally from os.getenv("OPENAI_API_KEY")
    model=embed_model)   # matches your embed_dim=1536 in PGVectorStore

    source = DocumentStream(name=filename, stream=buffer)
    result = converter.convert(source)  # pass the stream, not a path or llama-index Documents
    markdown_output = result.document.export_to_markdown()

    # 3. Wrap the markdown string back into a llama-index Document
    documents = [Document(text=markdown_output, metadata={"file_name": filename})]

    # 4. Index as before
    vector_store = PGVectorStore.from_params(
        database=db_name,
        host=host,
        user=db_user,
        password=db_password,
        port=db_port,
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