from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import authenticate
from repository.chat_repo import ChatManageLayer
from repository.doc_repo import (DocLayer,
                                 UploadDoc,
                                 UploadMain)
from repository.folder_repo import FolderLayer
from repository.message_repo import (ChatLayer,
                                     ChatApp,
                                     MessageApp)

import psycopg2.pool
import psycopg2
import os
import shutil
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5173/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=20,
        host='localhost',
        dbname='myragdb',
        user='postgres',
        password='Aalam357!POSTGRES',
        port=5432
    )
    logger.info("✅ Database pool created successfully")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
    raise

def get_conn():
    """
    FastAPI dependency: hand out a connection from the pool for the
    duration of a single request, and always return it afterwards.
    This replaces holding one global `conn` for the whole app's lifetime,
    which is not safe across concurrent requests.
    """
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)


class FolderCreate(BaseModel):
    name: str

class RenameFolder(BaseModel):
    name: str

class ChatCreate(BaseModel):
    title: str

class UserMessage(BaseModel):
    content: str

### FOLDERS

@app.post("/folders")
def create_new_folder(body: FolderCreate, user_id: str = Depends(authenticate), conn=Depends(get_conn)):
    folder_layer = FolderLayer(conn)
    try:
        row = folder_layer.create_new_folder(user_id, body.name)
        return {
            "id": row[0],
            "name": row[2],
            "user_id": row[1]
        }
    except Exception:
        logger.exception("create_new_folder route failed")
        raise HTTPException(status_code=500, detail="Failed to create folder")

@app.patch("/folders/{folder_id}")
def rename_folder(body: RenameFolder, folder_id: str, user_id: str = Depends(authenticate), conn=Depends(get_conn)):
    folder_layer = FolderLayer(conn)
    try:
        return folder_layer.rename_folder(body.name, folder_id)
    except Exception:
        logger.exception("rename_folder route failed")
        raise HTTPException(status_code=500, detail="Failed to rename folder")

@app.get("/folders")
def get_users_folders(user_id: str = Depends(authenticate), conn=Depends(get_conn)):
    folder_layer = FolderLayer(conn)
    try:
        return folder_layer.get_users_folders(user_id)
    except Exception:
        logger.exception("get_users_folders route failed")
        raise HTTPException(status_code=500, detail="Failed to fetch folders")

@app.delete("/folders/{folder_id}")
def delete_folder(folder_id: str, user_id: str = Depends(authenticate), conn=Depends(get_conn)):
    folder_layer = FolderLayer(conn)
    try:
        folder_layer.delete_folder(folder_id)
        return
    except Exception:
        logger.exception("delete_folder route failed")
        raise HTTPException(status_code=500, detail="Failed to delete folder")

### CHATS

@app.get("/folders/{folder_id}/chats")
def list_chats(folder_id: str, user_id: str = Depends(authenticate), conn=Depends(get_conn)):
    chat_manage_layer = ChatManageLayer(conn)
    try:
        return chat_manage_layer.list_chats(folder_id)
    except Exception:
        logger.exception("list_chats route failed")
        raise HTTPException(status_code=500, detail="Failed to fetch chats")

@app.post("/folders/{folder_id}/chats")
def create_new_chat(folder_id: str, body: ChatCreate, user_id: str = Depends(authenticate), conn=Depends(get_conn)):
    chat_manage_layer = ChatManageLayer(conn)
    try:
        return chat_manage_layer.create_new_chat(folder_id, body.title)
    except Exception:
        logger.exception("create_new_chat route failed")
        raise HTTPException(status_code=500, detail="Failed to create chat")

@app.delete("/chats/{chat_id}")
def delete_chats(chat_id: str, user_id: str = Depends(authenticate), conn=Depends(get_conn)):
    chat_manage_layer = ChatManageLayer(conn)
    try:
        chat_manage_layer.delete_chat(chat_id)
        return
    except Exception:
        logger.exception("delete_chats route failed")
        raise HTTPException(status_code=500, detail="Failed to delete chat")

### DOCUMENTS
         
@app.get("/folders/{folder_id}/documents")
def list_docs_main(folder_id: str, 
                   user_id: str = Depends(authenticate), 
                   conn=Depends(get_conn)):
    doc_app = DocLayer(conn)
    try:
        return doc_app.list_docs(folder_id)
    except Exception:
            logger.exception("list_docs failed")
            raise HTTPException(status_code=500, detail="Failed to generate response")

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/folders/{folder_id}/documents")
def upload_file(folder_id: str, file: UploadFile = File(...), user_id: str = Depends(authenticate), conn=Depends(get_conn)):
    upload_file_app = UploadMain(upload_file_cls=UploadDoc)

    try:
        return upload_file_app.upload_function(folder_id, file, conn)
    except Exception:
            logger.exception("upload_function failed")
            raise HTTPException(status_code=500, detail="Failed to generate response")

### MESSAGES

@app.get("/chats/{chat_id}/messages")
def list_messages_main(chat_id: str, user_id: str = Depends(authenticate), conn=Depends(get_conn)): 

    message_app = MessageApp(conn)

    try:
        return message_app.list_messages(chat_id)
    except Exception:
            logger.exception("list_messages failed")
            raise HTTPException(status_code=500, detail="Failed to generate response")

@app.post("/chats/{chat_id}/messages")
def gen_res_main(chat_id: str, body: UserMessage, user_id: str = Depends(authenticate), conn=Depends(get_conn)) -> dict:
    """
    Generate the appropriate response for the user's message.
    """
    chat_app = ChatApp(chat_layer_cls=ChatLayer)
    # ChatApp stores the class so it can build a new instance per request
    # if you stored a single instance, you would not automatically get a new connection each time

    try:
        return chat_app.gen_res(chat_id, body, conn)
    except Exception:
        logger.exception("gen_res_main failed")
        raise HTTPException(status_code=500, detail="Failed to generate response")