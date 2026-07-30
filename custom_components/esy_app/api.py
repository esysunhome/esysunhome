from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientSession

_LOGGER = logging.getLogger(__name__)


class EsyAppApiError(Exception):
    """Raised when an ESY API request fails."""


class EsyAppApiClient:
    """Async client for the esysunhome service."""

    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._token = token.strip() if token else None
        self._username = username.strip() if username else None
        self._password = password

    async def login(self) -> str:
        """Authenticate with the backend and store the returned bearer token."""
        if not self._username or not self._password:
            raise EsyAppApiError("Username and password are required")

        login_attempts = (
            (
                "/login?grant_type=app",
                {
                    "password": self._password,
                    "clientId": "",
                    "requestType": 1,
                    "loginType": "PASSWORD",
                    "userType": 2,
                    "userName": self._username,
                },
            ),
            (
                "/admin/login",
                {
                    "username": self._username,
                    "password": self._password,
                },
            ),
        )

        last_error: Exception | None = None
        for path, payload in login_attempts:
            try:
                response = await self._request_public("POST", path, json=payload)
                token = self._extract_token(response)
                if token:
                    self._token = token
                    return token
                last_error = EsyAppApiError("Login response did not include a token")
            except EsyAppApiError as err:
                last_error = err

        raise EsyAppApiError(f"Login failed: {last_error}")

    async def get_devices(self) -> list[dict[str, Any]]:
        """Fetch devices bound to the current account."""
        payload = await self._request("GET", "/api/lsydevice/page", params={"current": 1, "size": 100})
        return self._extract_list(payload)

    async def get_device_data(self, sn: str) -> dict[str, Any]:
        """Fetch current smart-home device data by SN."""
        payload = await self._request("GET", "/api/smart/home/device", params={"sn": sn})
        return payload if isinstance(payload, dict) else {}

    async def get_device_detail(self, device_id: str) -> dict[str, Any]:
        """Fetch app device detail by numeric device id."""
        payload = await self._request("GET", "/api/lsydevice/info", params={"id": device_id})
        return payload if isinstance(payload, dict) else {}

    async def get_mode_patterns(self, device_id: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Fetch available base operating modes from the backend."""
        try:
            return await self._request(
                "GET",
                "/api/lsypattern/page",
                params={"current": 1, "size": 50, "deviceId": device_id},
            )
        except EsyAppApiError:
            return await self._request("GET", "/api/lsypattern/page", params={"current": 1, "size": 50})

    async def set_base_mode(self, device_id: str, mode_code: int | str) -> dict[str, Any]:
        """Switch the inverter base operating mode via /api/lsypattern/switch."""
        payload = await self._request(
            "POST",
            "/api/lsypattern/switch",
            json={"deviceId": str(device_id), "code": mode_code},
        )
        return payload if isinstance(payload, dict) else {}

    async def get_power_data(self, device_id: str, date: str) -> list[dict[str, Any]]:
        """Fetch one day of power curve data for a device."""
        payload = await self._request(
            "GET",
            "/api/lsydevicepowerdata/list",
            params={"deviceId": device_id, "date": date},
        )
        return self._extract_list(payload)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        if not self._token:
            await self.login()

        try:
            return await self._request_authenticated(method, path, params=params, json=json)
        except EsyAppApiError as err:
            if "HTTP 401" not in str(err) or not self._username or not self._password:
                raise
            _LOGGER.info("ESY token expired or invalid, logging in again")
            await self.login()
            return await self._request_authenticated(method, path, params=params, json=json)

    async def _request_authenticated(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}
        return await self._send_request(method, url, headers=headers, params=params, json=json)

    async def _request_public(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        return await self._send_request(method, url, json=json)

    async def _send_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
                timeout=20,
            ) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise EsyAppApiError(f"HTTP {resp.status}: {text[:200]}")
                payload = await resp.json(content_type=None)
        except (ClientError, TimeoutError) as err:
            raise EsyAppApiError(str(err)) from err

        if not isinstance(payload, dict):
            raise EsyAppApiError("Invalid response payload")

        code = payload.get("code")
        if code not in (None, 0, 200):
            raise EsyAppApiError(str(payload.get("msg") or payload))

        data = payload.get("data")
        if data is None:
            return payload
        return data

    @staticmethod
    def _extract_list(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("records", "list", "rows", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        nested = payload.get("data")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
        if isinstance(nested, dict):
            return EsyAppApiClient._extract_list(nested)
        return []

    @staticmethod
    def _extract_token(payload: dict[str, Any] | list[Any]) -> str | None:
        """Extract a bearer token from common backend response shapes."""
        if not isinstance(payload, dict):
            return None
        candidates = [
            payload.get("token"),
            payload.get("access_token"),
            payload.get("accessToken"),
            payload.get("Authorization"),
            payload.get("authorization"),
        ]
        nested = payload.get("data")
        if isinstance(nested, dict):
            candidates.extend(
                [
                    nested.get("token"),
                    nested.get("access_token"),
                    nested.get("accessToken"),
                    nested.get("Authorization"),
                    nested.get("authorization"),
                ]
            )
        for token in candidates:
            if isinstance(token, str) and token.strip():
                token = token.strip()
                if token.lower().startswith("bearer "):
                    token = token[7:].strip()
                return token
        return None


