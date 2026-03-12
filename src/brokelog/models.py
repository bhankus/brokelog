from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    account: Mapped[str] = mapped_column(String, nullable=False)
    owner: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class TransactionBase(BaseModel):
    transaction_date: date
    amount: float
    description: str
    category: str
    type: str
    account: str
    owner: str

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v: object) -> str:
        val = str(v).lower()
        if val not in ("debit", "credit"):
            raise ValueError(f"type must be 'debit' or 'credit', got '{v}'")
        return val

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: object) -> float:
        result = float(str(v))
        if result == 0:
            raise ValueError("amount must be non-zero")
        return result


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class UploadResult(BaseModel):
    count: int
    transaction_ids: list[int]
