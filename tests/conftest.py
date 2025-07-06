import pytest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jarvus_app import create_app
from jarvus_app.db import db as _db

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session using the real app factory."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    with app.app_context():
        _db.create_all()
    yield app
    # Teardown
    with app.app_context():
        _db.drop_all()

@pytest.fixture(scope='session')
def db(app):
    """Provide the real db object for tests."""
    return _db

@pytest.fixture(scope='function')
def session(db, app):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    db.session = session
    yield session
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def test_client(app):
    """Create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_client_with_db(test_client, session):
    """Create a test client with database session."""
    yield test_client

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    yield
    # Cleanup
    if 'FLASK_ENV' in os.environ:
        del os.environ['FLASK_ENV']
    if 'TESTING' in os.environ:
        del os.environ['TESTING'] 