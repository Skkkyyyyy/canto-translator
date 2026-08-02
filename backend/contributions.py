"""User-submitted glossary entries: intake and duplicate lookup.

Nothing here writes to the glossary CSVs. Submissions go into SQLite with
status='pending' and only reach data/tokens100.csv once a human approves them.
"""

import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db import connect

router = APIRouter()

GLOSSARY_PATH = Path(__file__).parent / "data" / "tokens100.csv"


class SourceOutput(BaseModel):
    cantonese: str = ""
    mandarin: str = ""
    english: str = ""


class ContributionIn(BaseModel):
    kind: Literal["token", "sentence"]
    intent: Literal["new", "correction"] = "new"
    token: str = Field(max_length=300)
    cantonese: str = Field(default="", max_length=500)
    mandarin: str = Field(default="", max_length=500)
    english: str = Field(default="", max_length=500)
    function: str = Field(default="", max_length=50)
    example: str = Field(default="", max_length=500)
    note: str = Field(default="", max_length=2000)
    contributor: str = Field(default="", max_length=200)
    sourceText: str | None = Field(default=None, max_length=1000)
    sourceOutput: SourceOutput | None = None


class ContributionReceipt(BaseModel):
    id: str
    status: str
    createdAt: str


def load_glossary() -> list[dict]:
    """The same file rag.py matches against, read fresh so edits take effect."""
    if not GLOSSARY_PATH.exists():
        return []
    with GLOSSARY_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return [
            {
                "token": (row.get("token") or "").strip(),
                "cantonese": (row.get("Cantonese") or "").strip(),
                "mandarin": (row.get("Mandarin") or "").strip(),
                "english": (row.get("English") or "").strip(),
                "function": (row.get("Function") or "").strip(),
            }
            for row in csv.DictReader(handle)
            if (row.get("token") or "").strip()
        ]


@router.get("/glossary/search")
def glossary_search(q: str = ""):
    """Exact + prefix lookup, so the submit form can warn about duplicates."""
    needle = q.strip().lower()
    if not needle:
        return {"results": []}

    exact, prefix = [], []
    for row in load_glossary():
        token = row["token"].lower()
        if token == needle:
            exact.append(row)
        elif token.startswith(f"{needle} ") or needle.startswith(f"{token} "):
            prefix.append(row)

    return {"results": (exact + prefix)[:5]}


@router.post("/contributions", response_model=ContributionReceipt)
def create_contribution(payload: ContributionIn):
    token = payload.token.strip()
    if not token:
        raise HTTPException(422, "token is required")
    if not any(v.strip() for v in (payload.cantonese, payload.mandarin, payload.english)):
        raise HTTPException(422, "at least one of cantonese / mandarin / english is required")

    row_id = uuid.uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO contributions (
                id, kind, intent, token, cantonese, mandarin, english, function,
                example, note, contributor, source_text, source_output,
                status, created_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s)
            """,
            (
                row_id,
                payload.kind,
                payload.intent,
                token,
                payload.cantonese.strip(),
                payload.mandarin.strip(),
                payload.english.strip(),
                payload.function.strip(),
                payload.example.strip(),
                payload.note.strip(),
                payload.contributor.strip(),
                (payload.sourceText or "").strip(),
                payload.sourceOutput.model_dump_json() if payload.sourceOutput else "",
                created_at,
            ),
        )

    print(f"[contribution] {row_id} {payload.kind}/{payload.intent} {token!r}")
    return ContributionReceipt(id=row_id, status="pending", createdAt=created_at)
