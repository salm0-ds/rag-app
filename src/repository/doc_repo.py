from ingestion.s3 import uploads3
from ingestion.rag_ingestion import rag_pipeline

import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocLayer:

    def __init__ (self, conn):
        self.conn = conn

    def list_docs(self, folder_id: str):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT id, doc_name
                            FROM documents
                            WHERE folder_id = %s
                            """, 
                            (folder_id,))
                rows = cur.fetchall()
            return [{"id": r[0], "filename": r[1], "status": ""} for r in rows]
        except Exception:
            logger.exception("list_docs failed")
            raise

class UploadDoc:
    # get file name and file stream
    # if file uploaded to s3
    # push file through rag pipeline
    # set the folder id of data vector embeds
    # insert into documents 

    def __init__(self, conn):
        self.conn = conn

    def insert_doc_db(self, filename: str, folder_id: str):
        s3_address=os.getenv("S3_ADDRESS")
        doc_id_key=s3_address+filename

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            UPDATE data_vector_embeds 
                            SET folder_id = %s 
                            WHERE metadata_->>'doc_id' = %s;
                            """, 
                            (folder_id, doc_id_key))
                cur.execute("""
                            INSERT INTO documents (doc_name, folder_id) 
                            VALUES (%s, %s);         
                            """, 
                            (filename, folder_id))
                self.conn.commit()
            return "uploaded file"
        except Exception:
                logger.exception("insert_doc_db failed")
                raise
    
class UploadMain:

    def __init__(self, upload_file_cls) -> None:
        self.upload_file_cls = upload_file_cls

    def upload_function(self, folder_id: str, file) -> dict:
        filestream = file.file
        filename = file.filename

        if uploads3(file_stream=filestream, file_name=filename) is True:
            if rag_pipeline(filename=filename) is True:
                status = self.upload_file_cls(filename, folder_id)
            else:
                status = "unsuccesful rag upload"
        else:
            status = "unsuccesful s3 upload"
        
        return {
                "id": 1,
                "filename": filename,
                "status": status
            }
