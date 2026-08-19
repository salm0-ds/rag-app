import logging
import psycopg2.pool
import psycopg2
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.getenv("HOST")
db_name=os.getenv("DB_NAME")
db_user=os.getenv("DB_USER")
db_password=os.getenv("DB_PASSWORD")
db_port=os.getenv("DB_PORT")

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=20,
        host=host,
        dbname=db_name,
        user=db_user,
        password=db_password,
        port=db_port
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