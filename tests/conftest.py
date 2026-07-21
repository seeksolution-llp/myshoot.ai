import pytest
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import close_all_sessions

# Ensure your root project directory path is mapped into Python's lookup memory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(scope="session")
def event_loop():
    """Forces pytest-asyncio to maintain a singular, persistent loop context on Windows."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def clear_database_connections_after_test():
    """Defensive tear-down guard to ensure no dead connection handles cross tests."""
    yield
    await close_all_sessions()
