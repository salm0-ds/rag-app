from pydantic import BaseModel

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatManageLayer:
    """
    CRUD over chat rows (create/list/delete). Kept separate from ChatLayer,
    which handles the message-generation pipeline (insert message, decide,
    call the LLM, etc.) — different responsibilities, same conn-per-request pattern.
    """

    def __init__(self, conn):
        self.conn = conn

    def list_chats(self, folder_id: str):
        query = "SELECT id, summary FROM chats WHERE folder_id = %s"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (folder_id,))
                rows = cur.fetchall()
            return [{"id": r[0], "title": r[1]} for r in rows]
        except Exception:
            logger.exception("list_chats failed")
            raise

    def create_new_chat(self, folder_id: str, title: str):
        query = "INSERT INTO chats (folder_id, summary) VALUES (%s, %s) RETURNING id, summary;"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (folder_id, title))
                row = cur.fetchone()
                self.conn.commit()
            return {"id": row[0], "title": row[1]}
        except Exception:
            logger.exception("create_new_chat failed")
            raise

    def delete_chat(self, chat_id: str):
        query = "DELETE FROM chats WHERE id = %s;"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (chat_id,))
                self.conn.commit()
        except Exception:
            logger.exception("delete_chat failed")
            raise