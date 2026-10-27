from pathlib import Path
import os

from google import genai
from gemini_agent import ask_agent

from pydantic import BaseModel, Field
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, FileResponse
from report_service import generate_account_report
from chat_security import protect_chat_request
from access_control import require_production_access

from tool_registry import execute_tool
from typing import Literal
from pydantic import field_validator

app = FastAPI(
    title="InsightForge AI API",
    version="3.2.0",
    description="Local API for synthetic banking intelligence.",
)


@app.middleware("http")
async def private_demo_access(request: Request, call_next):
    """Protect every production route except the public health check."""
    denial = require_production_access(request)
    if denial is not None:
        return denial
    return await call_next(request)


@app.get("/api/health")
def health():
    """Check whether the Python server is running."""
    return {
        "status": "ok",
        "service": "insightforge-api",
    }


@lru_cache(maxsize=1)
def get_overview_data():
    """Read and cache the dataset overview."""
    return execute_tool("inspect_banking_data")


@app.get("/api/overview")
def overview():
    """Return real banking statistics from DuckDB."""
    try:
        return get_overview_data()

    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Banking dataset files are unavailable.",
        )

@lru_cache(maxsize=1)
def get_payment_data():
    """Read and cache the top 10 payment groups."""
    return execute_tool(
        "analyze_payment_formats",
        {"top_n": 10},
    )


@app.get("/api/payments")
def payments():
    """Return live payment statistics from DuckDB."""
    try:
        return get_payment_data()

    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Banking dataset files are unavailable.",
        )

class AccountInvestigationRequest(BaseModel):
    bank_id: int = Field(ge=0)
    account_number: str = Field(min_length=1, max_length=64)


@app.post("/api/accounts/investigate")
def investigate_account_api(request: AccountInvestigationRequest):
    """Investigate an account using the approved banking tool."""

    try:
        return execute_tool(
            "investigate_account",
            {
                "bank_id": request.bank_id,
                "account_number": request.account_number.strip(),
            },
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Banking dataset files are unavailable.",
        )

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail="Invalid account investigation details.",
        )


@app.post("/api/reports/account")
def account_report_pdf(request: AccountInvestigationRequest):
    """Download an evidence-backed PDF for one synthetic banking account."""
    account = request.account_number.strip()
    if not account:
        raise HTTPException(
            status_code=422,
            detail="Please enter an account number.",
        )

    try:
        pdf = generate_account_report(
            bank_id=request.bank_id,
            account_number=account,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Banking dataset files are unavailable.",
        ) from exc
    except Exception as exc:
        # Internal tool values, file paths and rendering errors stay private.
        raise HTTPException(
            status_code=500,
            detail="The account report could not be generated.",
        ) from exc

    if not isinstance(pdf, bytes) or not pdf.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=500,
            detail="The account report could not be generated.",
        )

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="InsightForge-Account-Report.pdf"'
            ),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value):
        if not value.strip():
            raise ValueError("Message text cannot be blank")
        return value.strip()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=6,
    )

@app.post("/api/chat")
def chat(request: ChatRequest, http_request: Request):
    """Ask the existing Gemini banking agent a question."""
    protect_chat_request(http_request)

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Please enter a question.",
        )

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini is not configured on the server.",
        )

    
    try:
        conversation_history = [
            message.model_dump()
            for message in request.history
        ]

        # Collect the approved tools used by Gemini.
        tool_activity = []

        with genai.Client(api_key=api_key) as client:
            answer = ask_agent(
                client,
                question,
                conversation_history=conversation_history,
                tool_activity=tool_activity,
            )

        return {
            "answer": answer,
            "tool_activity": tool_activity,
        }

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="The AI assistant could not complete the request.",
        )



# V3.9.5: Serve Vite's production build from the same origin as /api.
# FastAPI's existing authentication middleware protects these routes too.
# Keep using Vite on port 5173 during local development if preferred.
DASHBOARD_DIST = Path(__file__).resolve().parent / "dashboard" / "dist"


def _dashboard_html():
    index_file = DASHBOARD_DIST / "index.html"
    if not index_file.is_file():
        raise HTTPException(
            status_code=503,
            detail="Dashboard production build is unavailable.",
        )
    return FileResponse(
        index_file,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/", include_in_schema=False)
def dashboard_home():
    """Serve React's built index.html on the backend origin."""
    return _dashboard_html()


@app.get("/{frontend_path:path}", include_in_schema=False)
def dashboard_static_or_route(frontend_path: str):
    """Serve build assets or React client routes, never arbitrary local files."""
    if frontend_path == "api" or frontend_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found.")

    # Reject dotfiles, parent-directory traversal and symlink escapes.
    if any(part.startswith(".") for part in Path(frontend_path).parts):
        raise HTTPException(status_code=404, detail="Not found.")

    dist_root = DASHBOARD_DIST.resolve()
    requested = (dist_root / frontend_path).resolve()
    try:
        requested.relative_to(dist_root)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Not found.") from exc

    if requested.is_file():
        # Only built assets receive long-lived private caching.
        cache = (
            "private, max-age=31536000, immutable"
            if frontend_path.startswith("assets/")
            else "no-store"
        )
        return FileResponse(
            requested,
            headers={
                "Cache-Control": cache,
                "X-Content-Type-Options": "nosniff",
            },
        )

    # Client-side React routes need index.html on direct navigation/refresh.
    # Do not turn requests for missing assets into success responses.
    if "." not in Path(frontend_path).name and not frontend_path.startswith("assets/"):
        return _dashboard_html()

    raise HTTPException(status_code=404, detail="Not found.")
