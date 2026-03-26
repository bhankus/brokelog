import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from brokelog.database import get_db
from brokelog.main import app
from brokelog.models import Base

# ---------------------------------------------------------------------------
# Sample CSV data
# ---------------------------------------------------------------------------

CHASE_CSV_CONTENT = """\
Transaction Date,Post Date,Description,Category,Type,Amount,Memo
01/15/2024,01/16/2024,AMAZON.COM,Shopping,Sale,-45.99,
01/16/2024,01/17/2024,WHOLE FOODS,,Sale,-82.14,
01/20/2024,01/21/2024,PAYROLL,Income,Payment,2500.00,
"""

CHASE_CSV_MISSING_COLUMN = """\
Post Date,Description,Category,Amount,Memo
01/16/2024,AMAZON.COM,Shopping,-45.99,
"""

CHASE_CSV_EMPTY = """\
Transaction Date,Post Date,Description,Category,Type,Amount,Memo
"""

AMEX_CSV_CONTENT = """\
Date,Description,Amount,Extended Details,Appears On Your Statement As,Address,City/State,Zip Code,Country,Reference,Category
01/15/24,AMAZON.COM,45.99,,,,,,,,Shopping
01/16/24,WHOLE FOODS,82.14,,,,,,,,Groceries
01/20/24,PAYMENT - THANK YOU,-500.00,,,,,,,,Payments
"""

AMEX_CSV_MISSING_COLUMN = """\
Description,Amount
AMAZON.COM,45.99
"""

BARCLAYS_CSV_CONTENT = """\
Barclays Bank Delaware
Account Number: XXXXXXXXXXXX1234
Account Balance as of March 17 2026:    $12.34

Transaction Date,Description,Category,Amount
03/11/2026,"Audible*A25PO5B12","DEBIT",-14.95
03/03/2026,"FAVORITE RESTAURANT","DEBIT",-99.95
02/25/2026,"PAYMENT RECV'D CHECKFREE","CREDIT",100.50
"""

BARCLAYS_CSV_MISSING_COLUMN = """\
Barclays Bank Delaware
Account Number: XXXXXXXXXXXX1234
Account Balance as of March 17 2026:    $12.34

Description,Amount
AUDIBLE,-14.95
"""

CAPITAL_ONE_CSV_CONTENT = """\
Account Number,Transaction Description,Transaction Date,Transaction Type,Transaction Amount,Balance
4321,Electronic Payment to Gas & Electric,03/17/26,Debit,51.99,1234.56
4321,Electronic Payment to American Express,03/02/26,Debit,127.20,1234.557
4321,Withdrawal from T-MOBILE,03/02/26,Debit,187.76,1234.58
4321,Monthly Interest Paid,02/28/26,Credit,1.23,1234.59
"""

CAPITAL_ONE_CSV_MISSING_COLUMN = """\
Account Number,Transaction Description,Transaction Date,Balance
4321,Some Transaction,03/17/26,1234.56
"""

USAA_CSV_CONTENT = """\
Date,Description,Original Description,Category,Amount,Status
2026-03-20,ATM Withdrawal,Name of bank,Cash,-101.00,Posted
2026-03-20,ATM Fee Rebate,ATM REBATE,Atm Fee,1.00,Posted
2026-03-12,Interest Paid,INTEREST PAID,Interest Income,0.47,Posted
"""

USAA_CSV_MISSING_COLUMN = """\
Date,Description,Amount,Status
2026-03-20,ATM Withdrawal,-101.00,Posted
"""

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
