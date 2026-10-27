import os

from google import genai
from gemini_agent import ask_agent

from pydantic import BaseModel, Field
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from report_service import generate_account_report

from tool_registry import execute_tool
from typing import Literal
from pydantic import field_validator

app = FastAPI(
    title="InsightForge AI API",
    version="3.2.0",
    description="Local API for synthetic banking intelligence.",
)


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
def chat(request: ChatRequest):
    """Ask the existing Gemini banking agent a question."""

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

