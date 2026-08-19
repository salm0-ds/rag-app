import os
import logging

from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import HTTPException, Request, Depends
from db_conn import get_conn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clerk_sdk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))
authorised_parties = os.getenv("ADDRESS")

def authenticate(request: Request, conn = Depends(get_conn)) -> str:
    # connect to clerk
    request_state = clerk_sdk.authenticate_request(
        request,
        AuthenticateRequestOptions(
            authorized_parties=[authorised_parties]
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


