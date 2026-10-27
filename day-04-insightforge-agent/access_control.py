"""Private production access gate for InsightForge AI.

Intended for the FastAPI app when serving the React dashboard and API on
one HTTPS origin. Does not run automatically until wired into api.py.
Never place access credentials in frontend code or Git.
"""

import base64
import binascii
import hmac
import os

from fastapi import Request
from fastapi.responses import JSONResponse, Response


def require_production_access(request: Request) -> Response | None:
    """Return a rejection response, or None to let a request proceed.

    In production, all routes except GET /api/health require valid browser
    HTTP Basic credentials. Set credentials through server environment vars.
    Basic authentication must only be used behind HTTPS in production.
    """
    if os.getenv("INSIGHTFORGE_ENV", "development").strip().lower() != "production":
        return None

    if request.method == "GET" and request.url.path == "/api/health":
        return None

    username = os.getenv("INSIGHTFORGE_ACCESS_USERNAME", "").strip()
    password = os.getenv("INSIGHTFORGE_ACCESS_PASSWORD", "")

    if not username or ":" in username or len(password) < 16:
        return JSONResponse(
            status_code=503,
            content={"detail": "Production access is not configured."},
            headers={"Cache-Control": "no-store"},
        )

    deny = JSONResponse(
        status_code=401,
        content={"detail": "Authentication required."},
        headers={
            "WWW-Authenticate": 'Basic realm="InsightForge Private Demo", charset="UTF-8"',
            "Cache-Control": "no-store",
        },
    )

    authorization = request.headers.get("authorization", "")
    scheme, separator, encoded_credentials = authorization.partition(" ")
    if not separator or scheme.lower() != "basic" or not encoded_credentials:
        return deny

    try:
        decoded = base64.b64decode(
            encoded_credentials.strip(), validate=True
        ).decode("utf-8")
        submitted_user, colon, submitted_password = decoded.partition(":")
    except (binascii.Error, UnicodeError, ValueError):
        return deny

    if not colon:
        return deny

    user_matches = hmac.compare_digest(
        submitted_user.encode("utf-8"), username.encode("utf-8")
    )
    password_matches = hmac.compare_digest(
        submitted_password.encode("utf-8"), password.encode("utf-8")
    )
    if not (user_matches and password_matches):
        return deny

    return None
