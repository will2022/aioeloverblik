import time

import pytest
from httpx import Response

# --- Token Handling Tests ---


@pytest.mark.asyncio
async def test_token_caching_and_expiry(client, respx_mock, create_jwt):
    # Valid Token Scenario
    valid_jwt = create_jwt(time.time() + 3600)  # Expires in 1 hour
    token_route = respx_mock.get("/customerapi/api/token").mock(
        return_value=Response(200, json={"result": valid_jwt, "success": True, "errorCode": 0}),
    )

    t1 = await client._get_access_token()
    assert t1 == valid_jwt
    assert token_route.call_count == 1

    t2 = await client._get_access_token()
    assert t2 == valid_jwt
    assert token_route.call_count == 1

    # Expired Token Scenario
    client._token_expiry = time.time() - 100
    new_jwt = create_jwt(time.time() + 3600)

    token_route.side_effect = None
    token_route.return_value = Response(200, json={"result": new_jwt, "success": True, "errorCode": 0})

    t3 = await client._get_access_token()
    assert t3 == new_jwt


@pytest.mark.asyncio
async def test_token_optimistic_retry(client, respx_mock, create_jwt):
    """Test that 401 triggers retry even if local expiry check passes."""
    valid_jwt = create_jwt(time.time() + 3600)
    respx_mock.get("/customerapi/api/token").mock(
        return_value=Response(200, json={"result": valid_jwt, "success": True, "errorCode": 0}),
    )

    route = respx_mock.get("/customerapi/api/isalive")
    route.side_effect = [Response(401), Response(200, json={"result": True, "success": True})]

    is_alive = await client.is_alive()
    assert is_alive.get("result") is True
    assert route.call_count == 2


# --- Customer Client Tests ---


@pytest.mark.asyncio
async def test_get_metering_points(client, respx_mock):
    respx_mock.get("/customerapi/api/token").mock(return_value=Response(200, json={"result": "jwt", "success": True}))

    respx_mock.get("/customerapi/api/meteringpoints/meteringpoints?includeAll=false").mock(
        return_value=Response(
            200,
            json={
                "result": [{"meteringPointId": "123", "streetName": "Road"}],
                "success": True,
            },
        ),
    )

    mps = await client.get_metering_points()
    assert len(mps) == 1
    assert mps[0].metering_point_id == "123"


# --- Third Party Client Tests ---


@pytest.mark.asyncio
async def test_thirdparty_get_ids_strict_type(third_party_client, respx_mock):
    respx_mock.get("/thirdpartyapi/api/token").mock(return_value=Response(200, json={"result": "jwt", "success": True}))

    respx_mock.get("/thirdpartyapi/api/authorization/authorization/meteringpointids/customerKey/123").mock(
        return_value=Response(200, json={"result": ["MP1", "MP2"], "success": True}),
    )

    ids = await third_party_client.get_metering_point_ids(scope="customerKey", identifier="123")
    assert ids == ["MP1", "MP2"]
    assert isinstance(ids, list)
    assert isinstance(ids[0], str)


@pytest.mark.asyncio
async def test_thirdparty_get_metering_points(third_party_client, respx_mock):
    respx_mock.get("/thirdpartyapi/api/token").mock(return_value=Response(200, json={"result": "jwt", "success": True}))

    respx_mock.get("/thirdpartyapi/api/authorization/authorization/meteringpoints/authorizationId/auth1").mock(
        return_value=Response(200, json={"result": [{"meteringPointId": "999"}], "success": True}),
    )

    mps = await third_party_client.get_metering_points(scope="authorizationId", identifier="auth1")
    assert len(mps) == 1
    assert mps[0].metering_point_id == "999"
