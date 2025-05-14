"""凯迪仕门锁集成主文件"""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .kaadas_api import KaadasAPI

_LOGGER = logging.getLogger(__name__)

DOMAIN = "kaadas_lock"
DATA_KEY_STATUS = "status"

PLATFORMS = ["binary_sensor", "sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置配置项"""
    token = entry.data.get("token")
    wifi_sn = entry.data.get("wifi_sn")
    uid = entry.data.get("uid")
    
    api = KaadasAPI(token, wifi_sn, uid)
    
    coordinator = KaadasDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置项"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

class KaadasDataUpdateCoordinator(DataUpdateCoordinator):
    """数据更新协调器"""
    
    def __init__(self, hass: HomeAssistant, api: KaadasAPI) -> None:
        """初始化协调器"""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.api = api
        self.entities = []
    
    async def _async_update_data(self):
        """更新数据"""
        try:
            status = await self.api.async_get_lock_status()
            return {
                DATA_KEY_STATUS: status
            }
        except Exception as e:
            raise UpdateFailed(f"更新门锁状态失败: {e}")    