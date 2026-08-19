import os
import logging

import psycopg2.pool
import psycopg2

from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import HTTPException, Request, Depends

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

clerk_sdk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

def authenticate(request: Request, conn = Depends(get_conn)) -> str:
    # connect to clerk
    request_state = clerk_sdk.authenticate_request(
        request,
        AuthenticateRequestOptions(
            authorized_parties=["http://localhost:5173"]
        ),
    )

    # if request state is not sign in, raise error 401
    if not request_state.is_signed_in:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request_state.payload["sub"]

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users_table (id)
                VALUES (%s)
                ON CONFLICT (id) DO NOTHING;
                """,
                (user_id,)
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise 

    return user_id


