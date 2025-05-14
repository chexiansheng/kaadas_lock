"""凯迪仕门锁API接口"""

import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any

_LOGGER = logging.getLogger(__name__)

class KaadasAPI:
    """凯迪仕门锁API客户端"""
    
    def __init__(self, token: str, wifi_sn: str, uid: str) -> None:
        """初始化API客户端"""
        self.token = token
        self.wifi_sn = wifi_sn
        self.uid = uid
        self.base_url = "https://api.kaadas.com.cn/kaadas-app"
        
    async def async_get_lock_status(self) -> Dict[str, Any]:
        """获取门锁状态"""
        url = f"{self.base_url}/lock/getLockStatus"
        headers = {
            "Content-Type": "application/json",
            "token": self.token,
        }
        data = {
            "wifiSn": self.wifi_sn,
            "uid": self.uid,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    if result.get("code") == 0 and result.get("data"):
                        return self._parse_lock_status(result["data"])
                    
                    _LOGGER.error("获取门锁状态失败: %s", result.get("message", "未知错误"))
                    return {"last_text": "获取状态失败", "last_time": "", "last_user": "", "battery": 0}
                    
        except aiohttp.ClientError as e:
            _LOGGER.error("API请求失败: %s", str(e))
            return {"last_text": "连接失败", "last_time": "", "last_user": "", "battery": 0}
        except Exception as e:
            _LOGGER.error("获取门锁状态发生未知错误: %s", str(e))
            return {"last_text": "未知错误", "last_time": "", "last_user": "", "battery": 0}
    
    def _parse_lock_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析门锁状态数据"""
        try:
            # 提取电池信息
            battery = data.get("battery", 0)
            
            # 提取最后一条记录
            records = data.get("recordList", [])
            last_record = records[0] if records else {}
            
            # 提取操作类型
            operation_type = last_record.get("operationType", "")
            operation_type_text = {
                1: "指纹",
                2: "密码",
                3: "NFC",
                4: "机械钥匙",
                5: "APP",
                6: "自动",
                7: "胁迫指纹",
                8: "童锁",
                9: "上提反锁",
                10: "门未关报警",
                11: "撬锁报警",
                12: "试错报警",
                13: "低电量报警",
                14: "电池耗尽",
                15: "恢复出厂设置",
                16: "用户添加",
                17: "用户删除",
                18: "用户修改",
                19: "管理员添加",
                20: "管理员删除",
                21: "管理员修改",
                22: "密码重置",
                23: "指纹重置",
                24: "NFC重置",
                25: "报警解除",
                26: "防猫眼锁定",
                27: "防猫眼解锁",
                28: "童锁锁定",
                29: "童锁解锁",
            }.get(operation_type, "未知")
            
            # 提取操作结果
            operation_result = last_record.get("operationResult", "")
            operation_result_text = {
                1: "成功",
                2: "失败",
            }.get(operation_result, "未知")
            
            # 提取用户名
            user_name = last_record.get("userName", "")
            
            # 提取操作时间
            operation_time = last_record.get("operationTime", "")
            
            # 构建操作文本
            if operation_type in [1, 2, 3, 4, 5]:
                # 开锁操作
                action_text = f"{operation_type_text}开锁"
            elif operation_type in [9, 26, 28]:
                # 锁定操作
                action_text = f"{operation_type_text}"
            elif operation_type in [27, 29]:
                # 解锁操作
                action_text = f"{operation_type_text}"
            elif operation_type in [10, 11, 12, 13, 14]:
                # 报警操作
                action_text = f"{operation_type_text}"
            else:
                # 其他操作
                action_text = f"{operation_type_text}"
            
            # 添加结果
            if operation_result == 1:
                action_text += "成功"
            elif operation_result == 2:
                action_text += "失败"
            
            return {
                "last_text": action_text,
                "last_time": operation_time,
                "last_user": user_name,
                "battery": battery,
            }
        except Exception as e:
            _LOGGER.error("解析门锁状态失败: %s", str(e))
            return {"last_text": "解析状态失败", "last_time": "", "last_user": "", "battery": 0}    