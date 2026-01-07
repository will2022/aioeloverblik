import base64
import json

import pytest
import respx

from aioeloverblik import EloverblikClient, EloverblikThirdPartyClient


@pytest.fixture
def create_jwt():
    def _create(exp_time: float):
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(json.dumps({"exp": exp_time}).encode()).decode().rstrip("=")
        return f"{header}.{payload}.signature"

    return _create


@pytest.fixture
async def client():
    async with EloverblikClient(refresh_token="fake_token") as c:
        yield c


@pytest.fixture
async def third_party_client():
    async with EloverblikThirdPartyClient(refresh_token="fake_token") as c:
        yield c


@pytest.fixture
def respx_mock():
    with respx.mock(base_url="https://api.eloverblik.dk") as mock:
        yield mock
