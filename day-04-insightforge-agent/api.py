from pydantic import BaseModel, Field
from functools import lru_cache

from fastapi import FastAPI, HTTPException

from tool_registry import execute_tool


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
