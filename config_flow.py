"""凯迪仕门锁配置流程"""

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_WIFI_SN,
    CONF_UID,
    CONF_USER_MAPPING,
)

_LOGGER = logging.getLogger(__name__)

class KaadasLockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """凯迪仕门锁配置流程处理"""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    
    def __init__(self):
        """初始化配置流程"""
        self.base_config = {}
        self.user_mapping = {}
        
    async def async_step_user(self, user_input=None) -> FlowResult:
        """用户配置步骤 - 基础配置"""
        errors = {}
        
        if user_input is not None:
            try:
                # 验证输入
                await self.async_set_unique_id(user_input[CONF_WIFI_SN])
                self._abort_if_unique_id_configured()
                
                # 保存基础配置
                self.base_config = {
                    CONF_TOKEN: user_input[CONF_TOKEN],
                    CONF_WIFI_SN: user_input[CONF_WIFI_SN],
                    CONF_UID: user_input[CONF_UID],
                    CONF_USER_MAPPING: self.user_mapping
                }
                
                # 如果已经添加了用户，直接完成配置
                if self.user_mapping:
                    return self.async_create_entry(
                        title=f"凯迪仕门锁 {user_input[CONF_WIFI_SN]}",
                        data=self.base_config
                    )
                
                # 否则进入添加用户步骤
                return await self.async_step_add_user()
                
            except Exception as e:
                errors["base"] = "认证失败，请检查输入信息"
                _LOGGER.error("配置验证失败: %s", str(e))
        
        # 定义基础配置表单
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_WIFI_SN): str,
                vol.Required(CONF_UID): str,
            }),
            errors=errors,
            description_placeholders={
                "title": "凯迪仕门锁配置",
                "description": "请输入凯迪仕门锁的基础配置信息",
                "CONF_TOKEN": "凯迪仕API令牌",
                "CONF_WIFI_SN": "门锁WiFi序列号",
                "CONF_UID": "用户ID"
            }
        )
        
    async def async_step_add_user(self, user_input=None) -> FlowResult:
        """添加用户步骤"""
        errors = {}
        
        if user_input is not None:
            try:
                kaadas_username = user_input["kaadas_username"]
                local_nickname = user_input["local_nickname"]
                
                if not kaadas_username or not local_nickname:
                    raise ValueError("用户名不能为空")
                elif kaadas_username in self.user_mapping:
                    raise ValueError("该凯迪仕用户名已存在")
                    
                # 添加到用户映射
                self.user_mapping[kaadas_username] = local_nickname
                
                # 更新基础配置中的用户映射
                self.base_config[CONF_USER_MAPPING] = self.user_mapping
                
                # 提供选项：添加更多用户或完成配置
                return self.async_show_menu(
                    step_id="add_user_complete",
                    menu_options={
                        "add_another": "添加另一个用户",
                        "finish_config": "完成配置"
                    },
                    description_placeholders={
                        "current_count": len(self.user_mapping)
                    }
                )
                
            except ValueError as ve:
                errors["base"] = str(ve)
            except Exception as e:
                errors["base"] = "添加用户失败，请重试"
                _LOGGER.error("添加用户失败: %s", str(e))
        
        return self.async_show_form(
            step_id="add_user",
            data_schema=vol.Schema({
                vol.Required("kaadas_username"): str,
                vol.Required("local_nickname"): str
            }),
            errors=errors,
            description_placeholders={
                "title": "添加用户映射",
                "description": "配置凯迪仕用户名与本地用户名的映射关系"
            }
        )
        
    async def async_step_add_user_complete(self, user_input=None) -> FlowResult:
        """添加用户完成后的选项"""
        if user_input is not None:
            if user_input["choice"] == "add_another":
                return await self.async_step_add_user()
            elif user_input["choice"] == "finish_config":
                # 直接创建配置项，不再尝试调用不存在的步骤
                return self.async_create_entry(
                    title=f"凯迪仕门锁 {self.base_config[CONF_WIFI_SN]}",
                    data=self.base_config
                )
        
        # 默认返回基础配置表单
        return await self.async_step_user()
        
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """获取选项流程"""
        return KaadasLockOptionsFlowHandler(config_entry)

class KaadasLockOptionsFlowHandler(config_entries.OptionsFlow):
    """凯迪仕门锁选项配置流程"""
    
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """初始化选项流程"""
        self._config_entry = config_entry
        self.current_mapping = config_entry.data.get(CONF_USER_MAPPING, {})
        self.users_list = list(self.current_mapping.items())
        
    async def async_step_init(self, user_input=None) -> FlowResult:
        """选项配置主界面"""
        errors = {}
        
        if user_input is not None:
            action = user_input.get("action")
            
            if action == "add":
                return await self.async_step_add_user()
            elif action == "edit":
                return await self.async_step_select_edit_user()
            elif action == "delete":
                return await self.async_step_select_delete_user()
            elif action == "edit_base":
                return await self.async_step_edit_base_config()
            elif action == "refresh":
                await self._async_trigger_refresh()
                return self.async_create_entry(title="", data={})
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action"): vol.In({
                    "edit_base": "修改门锁基本配置",
                    "add": "添加用户",
                    "edit": "修改用户",
                    "delete": "删除用户",
                    "refresh": "刷新门锁数据"
                })
            }),
            errors=errors,
            description_placeholders={
                "count": len(self.current_mapping),
                "max": 99,
                "wifi_sn": self._config_entry.data.get(CONF_WIFI_SN, "未知")
            }
        )
        
    async def async_step_edit_base_config(self, user_input=None) -> FlowResult:
        """编辑基础配置"""
        errors = {}
        current_data = self._config_entry.data
        
        if user_input is not None:
            try:
                # 更新配置
                updated_data = {
                    **current_data,
                    CONF_TOKEN: user_input[CONF_TOKEN],
                    CONF_WIFI_SN: user_input[CONF_WIFI_SN],
                    CONF_UID: user_input[CONF_UID],
                }
                
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data=updated_data
                )
                
                # 触发数据刷新
                await self._async_trigger_refresh()
                
                return self.async_create_entry(title="", data={})
                
            except Exception as e:
                errors["base"] = "更新配置失败，请重试"
                _LOGGER.error("更新配置失败: %s", str(e))
        
        return self.async_show_form(
            step_id="edit_base_config",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN, default=current_data.get(CONF_TOKEN, "")): str,
                vol.Required(CONF_WIFI_SN, default=current_data.get(CONF_WIFI_SN, "")): str,
                vol.Required(CONF_UID, default=current_data.get(CONF_UID, "")): str,
            }),
            errors=errors,
            description_placeholders={
                "title": "修改门锁基本配置",
                "description": "修改凯迪仕门锁的基础配置信息"
            }
        )
        
    async def async_step_add_user(self, user_input=None) -> FlowResult:
        """添加新用户映射"""
        errors = {}
        
        if user_input is not None:
            try:
                kaadas_username = user_input["kaadas_username"]
                local_nickname = user_input["local_nickname"]
                
                if not kaadas_username or not local_nickname:
                    raise ValueError("用户名不能为空")
                elif kaadas_username in self.current_mapping:
                    raise ValueError("该凯迪仕用户名已存在")
                    
                # 添加到用户映射
                self.current_mapping[kaadas_username] = local_nickname
                
                # 更新配置
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={
                        **self._config_entry.data,
                        CONF_USER_MAPPING: self.current_mapping
                    }
                )
                
                # 触发数据刷新
                await self._async_trigger_refresh()
                
                return self.async_create_entry(title="", data={})
            except ValueError as ve:
                errors["base"] = str(ve)
            except Exception as e:
                errors["base"] = "添加用户失败，请重试"
                _LOGGER.error("添加用户失败: %s", str(e))
        
        return self.async_show_form(
            step_id="add_user",
            data_schema=vol.Schema({
                vol.Required("kaadas_username"): str,
                vol.Required("local_nickname"): str
            }),
            errors=errors,
            description_placeholders={
                "title": "添加用户映射",
                "description": "配置凯迪仕用户名与本地用户名的映射关系"
            }
        )
        
    async def async_step_select_edit_user(self, user_input=None) -> FlowResult:
        """选择要编辑的用户"""
        if not self.current_mapping:
            return self.async_abort(reason="no_users_to_edit")
            
        if user_input is not None:
            edit_index = int(user_input["edit_index"])
            return await self.async_step_edit_user(edit_index)
        
        # 生成用户列表选项
        user_options = {
            str(i): f"{kaadas_username} → {entity_id}"
            for i, (kaadas_username, entity_id) in enumerate(self.users_list)
        }
        
        return self.async_show_form(
            step_id="select_edit_user",
            data_schema=vol.Schema({
                vol.Required("edit_index"): vol.In(user_options)
            }),
            description_placeholders={
                "count": len(self.current_mapping)
            }
        )
        
    async def async_step_edit_user(self, edit_index, user_input=None) -> FlowResult:
        """编辑现有用户映射"""
        try:
            kaadas_username, entity_id = self.users_list[edit_index]
        except IndexError:
            return self.async_abort(reason="invalid_user_index")
            
        errors = {}
        
        if user_input is not None:
            try:
                new_kaadas_username = user_input["kaadas_username"]
                new_local_nickname = user_input["local_nickname"]
                
                if not new_kaadas_username or not new_local_nickname:
                    raise ValueError("用户名不能为空")
                elif new_kaadas_username != kaadas_username and new_kaadas_username in self.current_mapping:
                    raise ValueError("该凯迪仕用户名已被其他映射使用")
                    
                # 更新映射
                self.current_mapping.pop(kaadas_username)
                self.current_mapping[new_kaadas_username] = new_local_nickname
                self.users_list = list(self.current_mapping.items())
                
                # 更新配置
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={
                        **self._config_entry.data,
                        CONF_USER_MAPPING: self.current_mapping
                    }
                )
                
                # 触发数据刷新
                await self._async_trigger_refresh()
                
                return self.async_create_entry(title="", data={})
            except ValueError as ve:
                errors["base"] = str(ve)
            except Exception as e:
                errors["base"] = "编辑用户失败，请重试"
                _LOGGER.error("编辑用户失败: %s", str(e))
        
        return self.async_show_form(
            step_id="edit_user",
            data_schema=vol.Schema({
                vol.Required("kaadas_username", default=kaadas_username): str,
                vol.Required("local_nickname", default=entity_id): str
            }),
            errors=errors,
            description_placeholders={
                "index": edit_index + 1,
                "count": len(self.current_mapping)
            }
        )
        
    async def async_step_select_delete_user(self, user_input=None) -> FlowResult:
        """选择要删除的用户"""
        if not self.current_mapping:
            return self.async_abort(reason="no_users_to_delete")
            
        if user_input is not None:
            delete_index = int(user_input["delete_index"])
            return await self.async_step_confirm_delete(delete_index)
        
        # 生成用户列表选项
        user_options = {
            str(i): f"{kaadas_username} → {entity_id}"
            for i, (kaadas_username, entity_id) in enumerate(self.users_list)
        }
        
        return self.async_show_form(
            step_id="select_delete_user",
            data_schema=vol.Schema({
                vol.Required("delete_index"): vol.In(user_options)
            }),
            description_placeholders={
                "count": len(self.current_mapping)
            }
        )
        
    async def async_step_confirm_delete(self, delete_index, user_input=None) -> FlowResult:
        """确认删除用户"""
        try:
            kaadas_username, entity_id = self.users_list[delete_index]
        except IndexError:
            return self.async_abort(reason="invalid_user_index")
            
        if user_input is not None:
            if user_input.get("confirm", False):
                try:
                    # 删除用户映射
                    self.current_mapping.pop(kaadas_username)
                    self.users_list = list(self.current_mapping.items())
                    
                    # 更新配置
                    self.hass.config_entries.async_update_entry(
                        self._config_entry,
                        data={
                            **self._config_entry.data,
                            CONF_USER_MAPPING: self.current_mapping
                        }
                    )
                    
                    # 触发数据刷新
                    await self._async_trigger_refresh()
                    
                    return self.async_create_entry(title="", data={})
                except Exception as e:
                    errors = {"base": "删除用户失败，请重试"}
                    _LOGGER.error("删除用户失败: %s", str(e))
            else:
                return self.async_abort(reason="delete_cancelled")
                
        return self.async_show_form(
            step_id="confirm_delete",
            data_schema=vol.Schema({
                vol.Required("confirm", default=False): bool
            }),
            description_placeholders={
                "user_name": f"{kaadas_username} ({entity_id})"
            }
        )
        
    async def _async_trigger_refresh(self):
        """触发数据刷新"""
        try:
            coordinator = self.hass.data[DOMAIN][self._config_entry.entry_id]
            await coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error("刷新数据失败: %s", str(e))    