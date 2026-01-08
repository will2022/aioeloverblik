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
    ApiResponse,
    AuthorizationDto,
    MeteringPoint,
    MeteringPointCharges,
    MeteringPointDetail,
    MeteringPointThirdParty,
    MyEnergyDataMarketDocument,
)

logger = logging.getLogger(__name__)


Aggregation = Literal["Actual", "Quarter", "Hour", "Day", "Month", "Year"]


class BaseClient:
    """Base client handling authentication and common HTTP operations.

    Args:
        refresh_token: The refresh token used to obtain access tokens.
        timeout: HTTP request timeout in seconds.
    """

    BASE_URL = "https://api.eloverblik.dk"

    def __init__(self, refresh_token: str, timeout: float = 120.0):
        self._refresh_token = refresh_token
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the underlying HTTP client."""
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
        """Get metering points for the authenticated user.

        Args:
            include_all: If True, merges actively linked metering points with non-linked
                metering points found in DataHub (via CPR/CVR lookup).
        """
        endpoint = f"/customerapi/api/meteringpoints/meteringpoints?includeAll={str(include_all).lower()}"
        data = await self._request("GET", endpoint)
        raw_list = data.get("result", [])
        return TypeAdapter(list[MeteringPoint]).validate_python(raw_list)

    async def add_relation(self, metering_point_id: str, web_access_code: str) -> bool:
        """Add relation using Web Access Code.

        Args:
            metering_point_id: The ID of the metering point.
            web_access_code: The web access code provided by the data owner.
        """
        endpoint = f"/customerapi/api/meteringpoints/meteringpoint/relation/add/{metering_point_id}/{web_access_code}"
        data = await self._request("PUT", endpoint)
        return data.get("result", "") == "Success"

    async def add_relations_by_cvr(self, metering_point_ids: list[str]) -> list[ApiResponse[str]]:
        """Add relations for metering points registered to the authenticated CPR/CVR.

        Args:
            metering_point_ids: List of metering point IDs to add relations for.
        """
        endpoint = "/customerapi/api/meteringpoints/meteringpoint/relation/add"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}
        data = await self._request("POST", endpoint, json=payload)
        return TypeAdapter(list[ApiResponse[str]]).validate_python(data.get("result", []))

    async def delete_relation(self, metering_point_id: str) -> bool:
        """Delete relation to a metering point.

        Args:
            metering_point_id: The ID of the metering point.
        """
        endpoint = f"/customerapi/api/meteringpoints/meteringpoint/relation/{metering_point_id}"
        data = await self._request("DELETE", endpoint)
        return data.get("result", False)

    async def get_details(self, metering_point_ids: list[str]) -> list[MeteringPointDetail]:
        """Get detailed information for specified metering points.

        Args:
            metering_point_ids: List of metering point IDs.
        """
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
        """Get charges (subscriptions, tariffs, fees) for specified metering points.

        Returns charges linked now or in the future. History of charge changes is not included.

        Args:
            metering_point_ids: List of metering point IDs.
        """
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
        """Returns CSV string of metering points.

        Args:
            metering_point_ids: List of metering point IDs.
        """
        endpoint = "/customerapi/api/meteringpoints/masterdata/export"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}
        return await self._request("POST", endpoint, json=payload)

    async def export_charges(self, metering_point_ids: list[str]) -> str:
        """Returns CSV string of charges.

        Args:
            metering_point_ids: List of metering point IDs.
        """
        endpoint = "/customerapi/api/meteringpoints/charges/export"
        payload = {"meteringPoints": {"meteringPoint": metering_point_ids}}
        return await self._request("POST", endpoint, json=payload)

    async def export_time_series(
        self,
        metering_point_ids: list[str],
        from_date: date,
        to_date: date,
        aggregation: Aggregation = "Hour",
    ) -> str:
        """Returns CSV/Excel export of time series.

        Args:
            metering_point_ids: List of metering point IDs.
            from_date: Start date.
            to_date: End date.
            aggregation: Resolution. Values: 'Actual', 'Quarter', 'Hour', 'Day', 'Month', 'Year'.
        """
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
        aggregation: Aggregation = "Hour",
    ) -> list[MyEnergyDataMarketDocument]:
        """Get time series data.

        Data is only available for the previous 5 years plus the current year.

        Args:
            metering_point_ids: List of metering point IDs.
            from_date: Start date.
            to_date: End date.
            aggregation: Resolution. Values: 'Actual', 'Quarter', 'Hour', 'Day', 'Month', 'Year'.
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
        """Checks if the Third Party API is operating normally."""
        endpoint = "/thirdpartyapi/api/isalive"
        data = await self._request("GET", endpoint)
        return data

    async def get_authorizations(self) -> list[AuthorizationDto]:
        """Get list of active authorizations (powers of attorney) granted by customers.

        Expired or deleted authorizations are not returned.
        """
        endpoint = "/thirdpartyapi/api/authorization/authorizations"
        data = await self._request("GET", endpoint)

        raw_list = data.get("result", [])
        return TypeAdapter(list[AuthorizationDto]).validate_python(raw_list)

    async def get_metering_points(
        self,
        scope: Literal["authorizationId", "customerCVR", "customerKey"],
        identifier: str,
    ) -> list[MeteringPointThirdParty]:
        """Get metering points with a specific scope.

        Args:
            scope: 'authorizationId', 'customerCVR', or 'customerKey'
            identifier: The ID/CVR/Key value
        """
        endpoint = f"/thirdpartyapi/api/authorization/authorization/meteringpoints/{scope}/{identifier}"
        data = await self._request("GET", endpoint)

        raw_list = data.get("result", [])
        return TypeAdapter(list[MeteringPointThirdParty]).validate_python(raw_list)

    async def get_metering_point_ids(
        self,
        scope: Literal["authorizationId", "customerCVR", "customerKey"],
        identifier: str,
    ) -> list[str]:
        """Get just the list of metering point IDs for a specific scope.

        Args:
            scope: 'authorizationId', 'customerCVR', or 'customerKey'
            identifier: The ID/CVR/Key value
        """
        endpoint = f"/thirdpartyapi/api/authorization/authorization/meteringpointids/{scope}/{identifier}"
        data = await self._request("GET", endpoint)
        list_obj = data.get("result", [])
        return TypeAdapter(list[str]).validate_python(list_obj)

    async def get_details(self, metering_point_ids: list[str]) -> list[MeteringPointDetail]:
        """Get detailed information for specified metering points.

        Args:
            metering_point_ids: List of metering point IDs.
        """
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
        """Get charges (subscriptions, tariffs, fees) for specified metering points.

        Returns charges linked now or in the future. History of charge changes is not included.

        Args:
            metering_point_ids: List of metering point IDs.
        """
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
        aggregation: Aggregation = "Hour",
    ) -> list[MyEnergyDataMarketDocument]:
        """Get time series data.

        Data is only available for the previous 5 years plus the current year.

        Args:
            metering_point_ids: List of metering point IDs.
            from_date: Start date.
            to_date: End date.
            aggregation: Resolution. Values: 'Actual', 'Quarter', 'Hour', 'Day', 'Month', 'Year'.
        """
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
