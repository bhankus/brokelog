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
