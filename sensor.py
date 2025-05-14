"""凯迪仕门锁传感器平台"""

import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE, DEVICE_CLASS_BATTERY

from .const import DOMAIN, DATA_KEY_STATUS
from . import KaadasDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """设置传感器实体"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        KaadasBatterySensor(coordinator, entry),
        KaadasLastActionSensor(coordinator, entry),
        KaadasLastUserSensor(coordinator, entry),
        KaadasBatteryStatusSensor(coordinator, entry),
        KaadasOperationTypeSensor(coordinator, entry),
    ]
    
    async_add_entities(entities)

class KaadasBatterySensor(CoordinatorEntity, SensorEntity):
    """电池电量传感器"""
    
    _attr_has_entity_name = True
    _attr_name = "电池电量"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    
    def __init__(self, coordinator: KaadasDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """初始化传感器"""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_battery"
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
    def native_value(self) -> int:
        """返回电池电量"""
        return self.coordinator.data.get(DATA_KEY_STATUS, {}).get("battery", 0)

class KaadasLastActionSensor(CoordinatorEntity, SensorEntity):
    """最后操作传感器"""
    
    _attr_has_entity_name = True
    _attr_name = "最后操作"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(self, coordinator: KaadasDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """初始化传感器"""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_action"
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
    def native_value(self) -> str:
        """返回最后操作"""
        return self.coordinator.data.get(DATA_KEY_STATUS, {}).get("last_text", "")

class KaadasLastUserSensor(CoordinatorEntity, SensorEntity):
    """最后操作用户传感器"""
    
    _attr_has_entity_name = True
    _attr_name = "最后操作用户"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(self, coordinator: KaadasDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """初始化传感器"""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_user"
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
    def native_value(self) -> str:
        """返回最后操作用户"""
        return self.coordinator.data.get(DATA_KEY_STATUS, {}).get("last_user", "")

class KaadasBatteryStatusSensor(CoordinatorEntity, SensorEntity):
    """电池状态传感器"""
    
    _attr_has_entity_name = True
    _attr_name = "电池状态"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(self, coordinator: KaadasDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """初始化传感器"""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_battery_status"
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
    def native_value(self) -> str:
        """返回电池状态"""
        battery = self.coordinator.data.get(DATA_KEY_STATUS, {}).get("battery", 0)
        
        if battery <= 10:
            return "电量极低"
        elif battery <= 20:
            return "电量低"
        elif battery <= 80:
            return "电量中等"
        else:
            return "电量充足"

class KaadasOperationTypeSensor(CoordinatorEntity, SensorEntity):
    """操作类型传感器"""
    
    _attr_has_entity_name = True
    _attr_name = "操作类型"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(self, coordinator: KaadasDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """初始化传感器"""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_operation_type"
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
    def native_value(self) -> str:
        """返回操作类型"""
        last_text = self.coordinator.data.get(DATA_KEY_STATUS, {}).get("last_text", "")
        
        if "指纹" in last_text:
            return "指纹"
        elif "密码" in last_text:
            return "密码"
        elif "NFC" in last_text:
            return "NFC"
        elif "机械钥匙" in last_text:
            return "机械钥匙"
        elif "APP" in last_text:
            return "APP"
        else:
            return "未知"    