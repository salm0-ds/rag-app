from search.rag_llm_decider import sum_prev_mes, search_decider
from search.search import rag_search
from search.llm import generate_llm_response

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatLayer:

    def __init__(self, conn):
        self.conn = conn

    def insert_message_db(self, user_message: str, chat_id: str) -> None:
        if not user_message:
            logger.error("insert_message_db: empty user_message")
            raise Exception("insert_message_db: empty user_message")

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (chat_id, chat_role, message)
                    VALUES (%s, %s, %s)
                    """,
                    (chat_id, 'user', user_message)
                )
                self.conn.commit()
        except Exception:
            logger.exception("insert_message_db failed")
            raise

    def get_chat_history(self, chat_id: str):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, chat_role, message FROM messages
                    WHERE chat_id = %s
                    ORDER BY created_at DESC
                    LIMIT 4
                    """,
                    (chat_id,)
                )
                rows = cur.fetchall()
                return rows
        except Exception:
            logger.exception("get_chat_history failed")
            raise

    def summarise_chat(self, rows=None) -> str:
        if not rows:
            # No history yet (e.g. first message in a chat) — nothing to summarise.
            return ""

        try:
            return sum_prev_mes(rows)
        except Exception:
            logger.exception("summarise_chat failed")
            raise
# search
    def decider(self, user_message: str) -> str:
        try:
            return search_decider(user_message)
        except Exception:
            logger.exception("decider failed")
            raise
# search
    def generate_response(self, user_message: str, context: str = None, chat_history=None) -> str:
        try:
            return generate_llm_response(user_message, context, chat_history)
        except Exception:
            logger.exception("generate_response failed")
            raise
# search
    def get_folder_id(self, chat_id: str):
        if not chat_id:
            logger.error("get_folder_id: missing chat_id")
            raise Exception("get_folder_id: missing chat_id")

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT folder_id
                    FROM chats
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (chat_id,)
                )
                row = cur.fetchone()
                return row[0] if row else None
        except Exception:
            logger.exception("get_folder_id failed")
            raise

    def rag_search(self, user_message: str, folder_id: str):
        try:
            return rag_search(user_message, folder_id)
        except Exception:
            logger.exception("rag_search failed")
            raise
# search
    def insert_ai_db(self, generated_response: str, chat_id: str):
        if not generated_response:
            logger.error("insert_ai_db: empty generated_response")
            raise Exception("insert_ai_db: empty generated_response")

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (chat_id, chat_role, message)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (chat_id, 'assistant', generated_response)
                )
                result = cur.fetchone()
                self.conn.commit()
                return result
        except Exception:
            logger.exception("insert_ai_db failed")
            raise

class ChatApp:

    def __init__(self, chat_layer_cls):
        # Store the class, not an instance bound to one global connection —
        # a fresh ChatLayer is built per-request using that request's pooled connection.
        self.chat_layer_cls = chat_layer_cls

    def gen_res(self, chat_id: str, body, conn) -> dict:
        if not chat_id:
            raise Exception("Chat not selected")
        if not body:
            raise Exception("Chat not selected")

        chat_layer = self.chat_layer_cls(conn)

        try:
            user_message = body.content

            chat_layer.insert_message_db(user_message, chat_id)
            chat_history = chat_layer.get_chat_history(chat_id)
            chat_sum = chat_layer.summarise_chat(chat_history)
            decision = chat_layer.decider(user_message)

            if decision.result == "llm_answer":
                generated_response = chat_layer.generate_response(user_message, chat_sum)
            elif decision.result == "rag_search":
                folder_id = chat_layer.get_folder_id(chat_id)
                context = chat_layer.rag_search(user_message, folder_id)
                generated_response = chat_layer.generate_response(user_message, chat_sum, context)
            else:
                raise Exception(f"Unknown decider result: {decision.result!r}")

            row = chat_layer.insert_ai_db(generated_response, chat_id)

            return {
                "id": row[0],
                "role": "assistant",
                "content": generated_response
            }

        except Exception:
            logger.exception("gen_res failed")
            raise

class MessageApp:

    def __init__(self, conn):
        self.conn = conn

    def list_messages(self, chat_id: str):
                with self.conn.cursor() as cur:
                    cur.execute(
                    """
                    SELECT id, chat_role, message 
                    FROM messages 
                    WHERE chat_id = %s
                    """,
                    (chat_id,))
                    rows = cur.fetchall()
        
                return [{"id": r[0], "role": r[1], "content": r[2]} for r in rows]