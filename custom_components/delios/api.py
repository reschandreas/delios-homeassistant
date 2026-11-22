"""Async API client for the Delios inverter."""
import base64
import json
import logging

import aiohttp

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class DeliosApiError(Exception):
    pass


class DeliosAuthError(DeliosApiError):
    pass


class DeliosApi:
    def __init__(self, host, username, password, session=None):
        self.host = host.rstrip("/")
        if not self.host.startswith("http"):
            self.host = f"http://{self.host}"
        self.username = username
        self.password = password
        self._session = session
        self._owns_session = session is None
        self.token = None
        self.expire = 0
        self.level = None

    async def _session_get(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self):
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def login(self):
        session = await self._session_get()
        creds = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        try:
            async with session.get(
                f"{self.host}{API_BASE}/token",
                headers={"Authorization": f"Basic {creds}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise DeliosAuthError(f"login failed: {resp.status}")
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise DeliosApiError(str(err)) from err
        self.token = data["api_key"]
        self.expire = data["expire"]
        self.level = data.get("level")
        return data

    async def _ensure_token(self):
        import time
        if not self.token or time.time() >= (self.expire or 0) - 60:
            await self.login()

    async def _get(self, path):
        await self._ensure_token()
        session = await self._session_get()
        try:
            async with session.get(
                f"{self.host}{path}",
                headers={"x-access-token": self.token},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    self.token = None
                    await self.login()
                    async with session.get(
                        f"{self.host}{path}",
                        headers={"x-access-token": self.token},
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp2:
                        if resp2.status != 200:
                            raise DeliosApiError(f"{path}: {resp2.status}")
                        return await resp2.json(content_type=None)
                if resp.status != 200:
                    raise DeliosApiError(f"{path}: {resp.status}")
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise DeliosApiError(str(err)) from err

    async def _put(self, path, body):
        await self._ensure_token()
        session = await self._session_get()
        try:
            async with session.put(
                f"{self.host}{path}",
                json=body,
                headers={"x-access-token": self.token},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise DeliosApiError(f"{path}: {resp.status}")
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise DeliosApiError(str(err)) from err

    async def dashboard(self):
        return await self._get(f"{API_BASE}/dashboard")

    async def status(self):
        return await self._get(f"{API_BASE}/status")

    async def alarms(self):
        return await self._get(f"{API_BASE}/alarms")

    async def info_system(self):
        return await self._get(f"{API_BASE}/info/system")

    async def info_totalizer(self):
        return await self._get(f"{API_BASE}/info/totalizer")

    async def info_firmware(self):
        return await self._get(f"{API_BASE}/info/firmware")

    async def system_status(self):
        return await self._get(f"{API_BASE}/system/status")

    async def change_password(self, new_password):
        return await self._put(f"{API_BASE}/user/password", {"password": new_password})