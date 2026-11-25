"""Data update coordinator for Delios."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DeliosApi, DeliosApiError
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DeliosCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: DeliosApi, scan_interval):
        super().__init__(
            hass,
            _LOGGER,
            name="Delios",
            update_interval=scan_interval if scan_interval is not None else DEFAULT_SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self):
        import asyncio

        last_err = None
        for attempt in range(2):
            try:
                dashboard = await self.api.dashboard()
                status = await self.api.status()
                alarms = await self.api.alarms()
                totalizer = await self.api.info_totalizer()
                firmware = await self.api.info_firmware()
                system_status = await self.api.system_status()
                return {
                    "dashboard": dashboard,
                    "status": status,
                    "alarms": alarms,
                    "totalizer": totalizer,
                    "firmware": firmware,
                    "system_status": system_status,
                }
            except DeliosApiError as err:
                last_err = err
                if attempt == 0:
                    await asyncio.sleep(2)
        raise UpdateFailed(str(last_err)) from last_err