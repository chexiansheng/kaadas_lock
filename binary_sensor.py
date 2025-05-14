"""凯迪仕门锁二进制传感器平台"""

import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DATA_KEY_STATUS, CONF_USER_MAPPING
from . import KaadasDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """设置二进制传感器实体"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # 创建门锁状态传感器
    entities = [KaadasLockBinarySensor(coordinator, entry)]
    
    # 获取用户映射
    user_mapping = entry.data.get(CONF_USER_MAPPING, {})
    
    # 为每个用户创建传感器
    for kaadas_username, local_name in user_mapping.items():
        entities.append(KaadasUserBinarySensor(coordinator, entry, kaadas_username, local_name))
    
    # 添加所有实体
    async_add_entities(entities)
    
    # 存储实体列表到协调器
    coordinator.entities = entities

class KaadasLockBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """门锁状态二进制传感器"""
    
    _attr_has_entity_name = True
    _attr_name = "门锁状态"
    _attr_device_class = BinarySensorDeviceClass.LOCK
    
    def __init__(self, coordinator: KaadasDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """初始化传感器"""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_lock_status"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": f"凯迪仕门锁 {entry.data.get('wifi_sn')}",
            "manufacturer": "凯迪仕",
            "model": "智能门锁",
        }
        
    @property
    def available(self) -> bool:
        """传感器是否可用"""
        return self.coordinator.last_update_success
        
    @property
    def is_on(self) -> bool:
        """返回传感器状态"""
        last_text = self.coordinator.data.get(DATA_KEY_STATUS, {}).get("last_text", "")
        return "已开锁" in last_text or "开锁" in last_text
        
    @property
    def extra_state_attributes(self) -> dict:
        """返回额外的状态属性"""
        status = self.coordinator.data.get(DATA_KEY_STATUS, {})
        return {
            "最后操作时间": status.get("last_time"),
            "最后操作": status.get("last_text"),
            "操作用户": status.get("last_user")
        }

class KaadasUserBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """用户开锁状态二进制传感器"""
    
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(
        self, 
        coordinator: KaadasDataUpdateCoordinator, 
        entry: ConfigEntry,
        kaadas_username: str,
        local_name: str
    ) -> None:
        """初始化传感器"""
        super().__init__(coordinator)
        self.entry = entry
        self.kaadas_username = kaadas_username
        self._attr_name = f"{local_name} 开锁状态"
        self._attr_unique_id = f"{entry.entry_id}_{kaadas_username}_user_status"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": f"凯迪仕门锁 {entry.data.get('wifi_sn')}",
            "manufacturer": "凯迪仕",
            "model": "智能门锁",
        }
        
    @property
    def available(self) -> bool:
        """传感器是否可用"""
        return self.coordinator.last_update_success
        
    @property
    def is_on(self) -> bool:
        """返回传感器状态"""
        status = self.coordinator.data.get(DATA_KEY_STATUS, {})
        return (
            self.kaadas_username in status.get("last_user", "") 
            and ("已开锁" in status.get("last_text", "") or "开锁" in status.get("last_text", ""))
        )
        
    @property
    def extra_state_attributes(self) -> dict:
        """返回额外的状态属性"""
        status = self.coordinator.data.get(DATA_KEY_STATUS, {})
        return {
            "最后操作时间": status.get("last_time"),
            "最后操作": status.get("last_text"),
            "凯迪仕用户名": self.kaadas_username
        }    