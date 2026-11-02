"""Pytest configuration and reusable fixtures for FitVoice test suite."""

import os
import tempfile
import pytest
from fitvoice.db.database import init_db
from fitvoice.db.repository import FitnessRepository
from fitvoice.db.seed_data import seed_benchmark_data
from fitvoice.clients.sarvam import SarvamClient


@pytest.fixture
def temp_db():
    """Create an isolated temporary SQLite database populated with benchmark data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_benchmark_data(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def repository(temp_db):
    """Instantiate repository tied to temporary test database."""
    return FitnessRepository(db_path=temp_db)


@pytest.fixture
def mock_sarvam_client():
    """Client configured in demo mode with predictable deterministic mock responses."""
    return SarvamClient(api_key="mock_demo_key", base_url="https://api.sarvam.ai")

