import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FolderLayer:

    def __init__(self, conn):
        self.conn = conn

    def create_new_folder(self, clerk_uid: str, name: str):
        query = "INSERT INTO folders (clerk_uid, name) VALUES (%s, %s) RETURNING id, clerk_uid, name;"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (clerk_uid, name))
                row = cur.fetchone()
                self.conn.commit()
            return row
        except Exception:
            logger.exception("create_new_folder failed")
            raise

    def rename_folder(self, new_name: str, folder_id: str):
        query = "UPDATE folders SET name = %s WHERE id = %s RETURNING id, name, clerk_uid;"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (new_name, folder_id))
                row = cur.fetchone()
                self.conn.commit()
            return {
            "id": row[0],
            "name": row[1],
            "user_id": row[2]
            }
        except Exception:
            logger.exception("rename_folder failed")
            raise

    def get_users_folders(self, user_id: str):
        query = "SELECT id, name, clerk_uid FROM folders WHERE clerk_uid = %s"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (user_id,))
                rows = cur.fetchall()
            return [{"id": r[0], "name": r[1], "user_id": r[2]} for r in rows]
        except Exception:
            logger.exception("get_users_folders failed")
            raise

    def delete_folder(self, folder_id: str):
        query = "DELETE FROM folders WHERE id = %s;"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (folder_id,))
                self.conn.commit()
        except Exception:
            logger.exception("delete_folder failed")
            raise