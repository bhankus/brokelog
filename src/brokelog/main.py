import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from brokelog.categorizer import load_categories
from brokelog.database import engine, init_db
from brokelog.routers.transactions import router as transactions_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    # One-time migration: add user_category column to existing databases.
    # SQLite raises OperationalError if the column already exists; we ignore it.
    with engine.connect() as conn:
        try:
            conn.execute(
                text(
                    "ALTER TABLE transactions"
                    " ADD COLUMN user_category TEXT NOT NULL DEFAULT 'UNCATEGORIZED'"
                )
            )
            conn.commit()
        except Exception:
            pass

    categories_path = os.getenv("CATEGORIES_FILE", "categories.json")
    app.state.categories = load_categories(categories_path)
    yield


app = FastAPI(
    title="brokelog",
    description="REST API for ingesting and categorizing banking transaction CSV exports.",
    version="0.1.0",
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

app.include_router(transactions_router)


@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
