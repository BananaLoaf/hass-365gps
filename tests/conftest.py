import os
from pathlib import Path

import aiohttp
import pytest
import pytest_asyncio
from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent / ".env")


@pytest.fixture
def credentials():
    username = os.environ.get("TEST_USERNAME")
    password = os.environ.get("TEST_PASSWORD")
    if not username or not password:
        pytest.skip("Env vars TEST_USERNAME and TEST_PASSWORD not set")
    return {"username": username, "password": password}


@pytest_asyncio.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session
