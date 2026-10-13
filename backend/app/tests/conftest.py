"""Test fixtures. Uses an isolated SQLite file so the full API can be
exercised end-to-end without Docker/Postgres/Neo4j - consistent with local
development on disk-constrained machines (see docs/architecture/adr on
local SQLite dev). Production deployments use Postgres (see
docker-compose.yml). The test DB is wired via FastAPI's dependency-override
mechanism rather than env-var timing, since app.core.config.get_settings()
is cached at first import and may already have been called by the time any
fixture runs.
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def test_engine():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def app(test_engine):
    import app.models  # noqa: F401
    from app.db.session import Base, get_db
    from app.main import app as fastapi_app

    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, future=True)

    def _get_test_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _get_test_db
    yield fastapi_app
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session(app, test_engine):
    """A raw SQLAlchemy session bound to the same test_engine the `client`
    fixture's API calls write to - for tests that need to assert on rows
    (e.g. QuantumRun) with no dedicated read endpoint yet. Depends on `app`
    (not just `test_engine`) so the schema is guaranteed to exist even if
    no `client` fixture in this test ever triggered it."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, future=True)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
