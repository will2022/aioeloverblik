import base64
import json
import logging
import time
from datetime import date
from typing import Any, Literal, Optional

import httpx
from pydantic import TypeAdapter

from .exceptions import AuthenticationError, EloverblikError, RateLimitError, ServerError
from .models import (
    Authorization,
    MeteringPoint,
    MeteringPointCharges,
    MeteringPointDetail,
    MyEnergyDataMarketDocument,
)

logger = logging.getLogger(__name__)


class BaseClient:
    """Base client handling authentication and common HTTP operations."""

    BASE_URL = "https://api.eloverblik.dk"

    def __init__(self, refresh_token: str, timeout: float = 120.0):
        self._refresh_token = refresh_token
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _get_access_token(self) -> str:
        """Exchanges refresh token for short-lived access token."""
        if self._access_token and self._token_expiry > time.time() + 60:
            return self._access_token

        url = f"{self.BASE_URL}{self.TOKEN_ENDPOINT}"
        headers = {
            "Authorization": f"Bearer {self._refresh_token}",
        }

        try:
            resp = await self._client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["result"]
            self._token_expiry = self._decode_token_expiry(self._access_token)
            return self._access_token
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid refresh token") from e
            raise ServerError(f"Failed to get token: {e}") from e

    def _decode_token_expiry(self, token: str) -> float:
        """Decode JWT payload to extract expiry time."""
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return 0.0

            payload = parts[1]
            payload += "=" * ((4 - len(payload) % 4) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)
            return float(claims.get("exp", 0))
        except Exception:
            # If decoding fails, assume expired/invalid to force refresh next time
            return 0.0

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Any = None,
        retry_auth: bool = True,
    ) -> dict[str, Any] | str:
        """Internal request helper with auto-reauth."""
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = await self._client.request(method, url, headers=headers, json=json)
            response.raise_for_status()

            # Helper for export endpoints that return CSV/Text
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return response.text

            data = response.json()
            # API usually returns { "success": boolean, "errorCode": int, ... }
            if isinstance(data, dict) and not data.get("success", True):
                msg = data.get("errorText") or "Unknown API error"
                code = data.get("errorCode")
                raise EloverblikError(f"API Error {code}: {msg}", error_code=code, response_text=str(data))

            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and retry_auth:
                # Token might have expired
                self._access_token = None
                return await self._request(method, endpoint, json, retry_auth=False)
            elif e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded") from e
            elif e.response.status_code >= 500:
                raise ServerError(f"Server error {e.response.status_code}") from e
            else:
                raise EloverblikError(f"HTTP Error {e.response.status_code}: {e.response.text}") from e


class EloverblikClient(BaseClient):
    """Client for the Customer API (own data)."""

    TOKEN_ENDPOINT = "/customerapi/api/token"

    async def is_alive(self) -> bool:
        """Checks if the API is operating normally."""
        endpoint = "/customerapi/api/isalive"
        data = await self._request("GET", endpoint)
        return data

    async def get_metering_points(self, include_all: bool = False) -> list[MeteringPoint]:
        endpoint = f"/customerapi/api/meteringpoints/meteringpoints?includeAll={str(include_all).lower()}"
        data = await self._request("GET", endpoint)
        raw_list = data.get("result", [])
        return TypeAdapter(list[MeteringPoint]).validate_python(raw_list)

    async def add_relation(self, metering_point_id: str, web_access_code: str) -> bool:
        """Add relation using Web Access Code."""
        endpoint = f"/customerapi/api/meteringpoints/meteringpoint/relation/add/{metering_point_id}/{web_access_code}"
        data = await self._request("PUT", endpoint)
        return data.get("result", "") == "Success"

    async def add_relations_by_cvr(self, metering_point_ids: list[str]) -> list[str]:
        """Add relations for metering points registered to the authenticated CPR/CVR."""
        endpoint = "/customerapi/api/meteringpoints/meteringpoint/relation/add"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}
        data = await self._request("POST", endpoint, json=payload)
        return TypeAdapter(list[str]).validate_python(data.get("result", []))

    async def delete_relation(self, metering_point_id: str) -> bool:
        endpoint = f"/customerapi/api/meteringpoints/meteringpoint/relation/{metering_point_id}"
        data = await self._request("DELETE", endpoint)
        return data.get("success", False)

    async def get_details(self, metering_point_ids: list[str]) -> list[MeteringPointDetail]:
        endpoint = "/customerapi/api/meteringpoints/meteringpoint/getdetails"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}

        data = await self._request("POST", endpoint, json=payload)

        items = data.get("result", [])
        results = []
        for item in items:
            if item.get("result"):
                results.append(item["result"])

        return TypeAdapter(list[MeteringPointDetail]).validate_python(results)

    async def get_charges(self, metering_point_ids: list[str]) -> list[MeteringPointCharges]:
        endpoint = "/customerapi/api/meteringpoints/meteringpoint/getcharges"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}

        data = await self._request("POST", endpoint, json=payload)

        items = data.get("result", [])
        results = []
        for item in items:
            if item.get("result"):
                results.append(item["result"])

        return TypeAdapter(list[MeteringPointCharges]).validate_python(results)

    async def export_metering_points(self, metering_point_ids: list[str]) -> str:
        """Returns CSV string of metering points."""
        endpoint = "/customerapi/api/meteringpoints/masterdata/export"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}
        return await self._request("POST", endpoint, json=payload)

    async def export_charges(self, metering_point_ids: list[str]) -> str:
        """Returns CSV string of charges."""
        endpoint = "/customerapi/api/meteringpoints/charges/export"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}
        return await self._request("POST", endpoint, json=payload)

    async def export_time_series(
        self,
        metering_point_ids: list[str],
        from_date: date,
        to_date: date,
        aggregation: str = "Hour",
    ) -> str:
        """Returns CSV/Excel export of time series."""
        fmt_from = from_date.strftime("%Y-%m-%d")
        fmt_to = to_date.strftime("%Y-%m-%d")
        endpoint = f"/customerapi/api/meterdata/timeseries/export/{fmt_from}/{fmt_to}/{aggregation}"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}
        return await self._request("POST", endpoint, json=payload)

    async def get_time_series(
        self,
        metering_point_ids: list[str],
        from_date: date,
        to_date: date,
        aggregation: str = "Hour",
    ) -> list[MyEnergyDataMarketDocument]:
        """
        Get time series data.
        Aggregation: 'Actual', 'Quarter', 'Hour', 'Day', 'Month', 'Year'
        """
        fmt_from = from_date.strftime("%Y-%m-%d")
        fmt_to = to_date.strftime("%Y-%m-%d")
        endpoint = f"/customerapi/api/meterdata/gettimeseries/{fmt_from}/{fmt_to}/{aggregation}"

        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}

        data = await self._request("POST", endpoint, json=payload)

        items = data.get("result", [])
        documents = []
        for item in items:
            doc = item.get("MyEnergyData_MarketDocument")
            if doc:
                documents.append(doc)

        return TypeAdapter(list[MyEnergyDataMarketDocument]).validate_python(documents)


class EloverblikThirdPartyClient(BaseClient):
    """Client for the ThirdParty API (accessing other's data)."""

    TOKEN_ENDPOINT = "/thirdpartyapi/api/token"

    async def is_alive(self) -> bool:
        endpoint = "/thirdpartyapi/api/isalive"
        data = await self._request("GET", endpoint)
        return data

    async def get_authorizations(self) -> list[Authorization]:
        endpoint = "/thirdpartyapi/api/authorization/authorizations"
        data = await self._request("GET", endpoint)

        raw_list = data.get("result", [])
        return TypeAdapter(list[Authorization]).validate_python(raw_list)

    async def get_metering_points(
        self,
        scope: Literal["authorizationId", "customerCVR", "customerKey"],
        identifier: str,
    ) -> list[MeteringPoint]:
        """
        Get metering points with a specific scope.

        :param scope: 'authorizationId', 'customerCVR', or 'customerKey'
        :param identifier: The ID/CVR/Key value
        """
        endpoint = f"/thirdpartyapi/api/authorization/authorization/meteringpoints/{scope}/{identifier}"
        data = await self._request("GET", endpoint)

        raw_list = data.get("result", [])
        return TypeAdapter(list[MeteringPoint]).validate_python(raw_list)

    async def get_metering_point_ids(
        self,
        scope: Literal["authorizationId", "customerCVR", "customerKey"],
        identifier: str,
    ) -> list[str]:
        """
        Get just the list of metering point IDs for a specific scope.

        :param scope: 'authorizationId', 'customerCVR', or 'customerKey'
        :param identifier: The ID/CVR/Key value
        """
        endpoint = f"/thirdpartyapi/api/authorization/authorization/meteringpointids/{scope}/{identifier}"
        data = await self._request("GET", endpoint)
        list_obj = data.get("result", [])
        return TypeAdapter(list[str]).validate_python(list_obj)

    async def get_details(self, metering_point_ids: list[str]) -> list[MeteringPointDetail]:
        endpoint = "/thirdpartyapi/api/meteringpoint/getdetails"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}

        data = await self._request("POST", endpoint, json=payload)

        items = data.get("result", [])
        results = []
        for item in items:
            if item.get("result"):
                results.append(item["result"])

        return TypeAdapter(list[MeteringPointDetail]).validate_python(results)

    async def get_charges(self, metering_point_ids: list[str]) -> list[MeteringPointCharges]:
        endpoint = "/thirdpartyapi/api/meteringpoint/getcharges"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}

        data = await self._request("POST", endpoint, json=payload)

        items = data.get("result", [])
        results = []
        for item in items:
            if item.get("result"):
                results.append(item["result"])

        return TypeAdapter(list[MeteringPointCharges]).validate_python(results)

    async def get_time_series(
        self,
        metering_point_ids: list[str],
        from_date: date,
        to_date: date,
        aggregation: str = "Hour",
    ) -> list[MyEnergyDataMarketDocument]:
        fmt_from = from_date.strftime("%Y-%m-%d")
        fmt_to = to_date.strftime("%Y-%m-%d")
        endpoint = f"/thirdpartyapi/api/meterdata/gettimeseries/{fmt_from}/{fmt_to}/{aggregation}"

        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}

        data = await self._request("POST", endpoint, json=payload)

        items = data.get("result", [])
        documents = []
        for item in items:
            doc = item.get("MyEnergyData_MarketDocument")
            if doc:
                documents.append(doc)

        return TypeAdapter(list[MyEnergyDataMarketDocument]).validate_python(documents)
