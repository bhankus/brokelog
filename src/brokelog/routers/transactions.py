import io

import pandas as pd
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from brokelog.database import get_db
from brokelog.models import Transaction, TransactionCreate, TransactionRead, UploadResult
from brokelog.parsers import get_parser

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


async def _handle_csv_upload(
    file: UploadFile,
    bank: str,
    account: str,
    owner: str,
    db: Session,
) -> UploadResult:
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV (.csv)")

    content = (await file.read()).decode("utf-8")
    try:
        df = pd.read_csv(io.StringIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {exc}") from exc

    parser = get_parser(bank)

    try:
        transaction_creates = parser.parse(df, account=account, owner=owner)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    orm_objects = [Transaction(**t.model_dump()) for t in transaction_creates]
    db.add_all(orm_objects)
    db.commit()
    for obj in orm_objects:
        db.refresh(obj)

    return UploadResult(
        count=len(orm_objects),
        transaction_ids=[obj.id for obj in orm_objects],
    )


async def _handle_json_create(request: Request, db: Session) -> TransactionRead:
    try:
        body = await request.json()
        transaction_create = TransactionCreate(**body)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    txn = Transaction(**transaction_create.model_dump())
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return TransactionRead.model_validate(txn)


@router.post("/", status_code=201)
async def create_transactions(
    request: Request,
    db: Session = Depends(get_db),
    # Form fields (only present for multipart requests)
    file: UploadFile | None = None,
    bank: str | None = Form(default=None),
    account: str | None = Form(default=None),
    owner: str | None = Form(default=None),
) -> UploadResult | TransactionRead:
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        if file is None or bank is None or account is None or owner is None:
            raise HTTPException(
                status_code=422,
                detail="Multipart upload requires: file, bank, account, owner",
            )
        return await _handle_csv_upload(file, bank, account, owner, db)

    # application/json path
    return await _handle_json_create(request, db)


@router.get("/", response_model=list[TransactionRead])
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    account: str | None = None,
    owner: str | None = None,
    db: Session = Depends(get_db),
) -> list[Transaction]:
    query = db.query(Transaction)
    if account is not None:
        query = query.filter(Transaction.account == account)
    if owner is not None:
        query = query.filter(Transaction.owner == owner)
    return query.offset(skip).limit(limit).all()


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)) -> Transaction:
    txn = db.get(Transaction, transaction_id)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)) -> Response:
    txn = db.get(Transaction, transaction_id)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(txn)
    db.commit()
    return Response(status_code=204)
