"""
疾病管理器核心模块
负责管理疾病状态、时间计算、状态转换等核心逻辑
"""

import time
import random
import logging
from typing import Optional, Dict, Any, List
from .illness_types import (
    IllnessType, IllnessInfo, get_illness_description,
    get_illness_duration, get_illness_severity, get_possible_transitions
)

logger = logging.getLogger(__name__)


class IllnessManager:
    """疾病管理器核心类"""
    
    def __init__(self, storage):
        """
        初始化疾病管理器
        
        Args:
            storage: 本地存储实例，用于持久化疾病状态
        """
        self.storage = storage
        self.current_illness: Optional[IllnessInfo] = None
        self.last_recovery_time: float = 0
        self.cool_down_end_time: float = 0
        
        # 从存储加载状态
        self.load_state()
    
    def load_state(self):
        """从本地存储加载疾病状态"""
        try:
            state_data = self.storage.get("illness_state", {})
            
            if state_data.get("current_illness"):
                illness_data = state_data["current_illness"]
                self.current_illness = IllnessInfo(
                    illness_type=IllnessType(illness_data["type"]),
                    start_time=illness_data["start_time"],
                    severity=illness_data.get("severity", 0.5),
                    stage=illness_data.get("stage", "initial")
                )
            
            self.last_recovery_time = state_data.get("last_recovery_time", 0)
            self.cool_down_end_time = state_data.get("cool_down_end_time", 0)
            
            logger.info(f"疾病状态已加载: {self.get_health_status()}")
            
        except Exception as e:
            logger.error(f"加载疾病状态失败: {e}")
            self.current_illness = None
            self.last_recovery_time = 0
            self.cool_down_end_time = 0
    
    def save_state(self):
        """保存疾病状态到本地存储"""
        try:
            state_data = {
                "current_illness": None,
                "last_recovery_time": self.last_recovery_time,
                "cool_down_end_time": self.cool_down_end_time,
                "last_update": time.time()
            }
            
            if self.current_illness:
                state_data["current_illness"] = {
                    "type": self.current_illness.illness_type.value,
                    "start_time": self.current_illness.start_time,
                    "severity": self.current_illness.severity,
                    "stage": self.current_illness.stage
                }
            
            self.storage.set("illness_state", state_data)
            logger.debug("疾病状态已保存")
            
        except Exception as e:
            logger.error(f"保存疾病状态失败: {e}")
    
    def update_illness_state(self):
        """更新疾病状态（考虑时间流逝）"""
        if not self.current_illness:
            return
        
        current_time = time.time()
        duration_hours = self.current_illness.get_duration_hours()
        illness_type = self.current_illness.illness_type
        expected_duration = get_illness_duration(illness_type)
        
        logger.debug(f"当前疾病: {illness_type.value}, 持续时间: {duration_hours:.1f}小时, 预期: {expected_duration}小时")
        
        # 检查是否应该转换到下一个疾病阶段
        if duration_hours >= expected_duration:
            possible_transitions = get_possible_transitions(illness_type)
            
            if possible_transitions:
                # 有转换可能，随机决定是否转换
                if random.random() < 0.7:  # 70%概率转换
                    new_illness_type = random.choice(possible_transitions)
                    self.transition_to_illness(new_illness_type)
                else:
                    # 直接康复
                    self.recover_from_illness()
            else:
                # 没有转换可能，直接康复
                self.recover_from_illness()
        
        # 更新疾病阶段
        self._update_illness_stage(duration_hours, expected_duration)
    
    def _update_illness_stage(self, duration_hours: float, expected_duration: float):
        """更新疾病阶段"""
        if not self.current_illness:
            return
        
        progress = duration_hours / expected_duration if expected_duration > 0 else 0
        
        if progress < 0.3:
            new_stage = "initial"
        elif progress < 0.7:
            new_stage = "progressing"
        else:
            new_stage = "recovering"
        
        if self.current_illness.stage != new_stage:
            self.current_illness.stage = new_stage
            logger.info(f"疾病阶段更新: {new_stage}")
            self.save_state()
    
    def transition_to_illness(self, new_illness_type: IllnessType):
        """转换到新的疾病"""
        old_illness = self.current_illness.illness_type.value if self.current_illness else "无"
        new_illness = new_illness_type.value
        
        self.current_illness = IllnessInfo(
            illness_type=new_illness_type,
            start_time=time.time(),
            severity=get_illness_severity(new_illness_type),
            stage="initial"
        )
        
        logger.info(f"疾病转换: {old_illness} -> {new_illness}")
        self.save_state()
    
    def recover_from_illness(self):
        """从疾病中康复"""
        if self.current_illness:
            illness_type = self.current_illness.illness_type.value
            duration = self.current_illness.get_duration_hours()
            
            logger.info(f"疾病康复: {illness_type}, 持续时间: {duration:.1f}小时")
            
            # 保存到历史记录
            self._add_to_history(self.current_illness, time.time())
            
            self.current_illness = None
            self.last_recovery_time = time.time()
            
            self.save_state()
    
    def _add_to_history(self, illness: IllnessInfo, end_time: float):
        """添加疾病到历史记录"""
        try:
            history = self.storage.get("illness_history", [])
            
            history_record = {
                "type": illness.illness_type.value,
                "start_time": illness.start_time,
                "end_time": end_time,
                "duration_hours": (end_time - illness.start_time) / 3600,
                "severity": illness.severity
            }
            
            history.append(history_record)
            
            # 只保留最近20条记录
            if len(history) > 20:
                history = history[-20:]
            
            self.storage.set("illness_history", history)
            
        except Exception as e:
            logger.error(f"添加疾病历史记录失败: {e}")
    
    def should_get_sick(self, daily_probability: float) -> bool:
        """检查是否应该生病"""
        current_time = time.time()
        
        # 检查冷却期
        if current_time < self.cool_down_end_time:
            remaining_hours = (self.cool_down_end_time - current_time) / 3600
            logger.debug(f"冷却期中，剩余时间: {remaining_hours:.1f}小时")
            return False
        
        # 检查当前是否已生病
        if self.current_illness:
            return False
        
        # 基于日常概率决定是否生病
        if random.random() < daily_probability:
            logger.info("触发新疾病")
            return True
        
        return False
    
    def trigger_random_illness(self) -> Optional[IllnessInfo]:
        """触发随机疾病"""
        try:
            # 获取随机疾病类型
            illness_type = self._get_weighted_random_illness()
            
            self.current_illness = IllnessInfo(
                illness_type=illness_type,
                start_time=time.time(),
                severity=get_illness_severity(illness_type),
                stage="initial"
            )
            
            logger.info(f"触发新疾病: {illness_type.value}")
            self.save_state()
            
            return self.current_illness
            
        except Exception as e:
            logger.error(f"触发随机疾病失败: {e}")
            return None
    
    def _get_weighted_random_illness(self) -> IllnessType:
        """获取加权随机疾病类型（轻微疾病概率更高）"""
        # 定义疾病权重（数值越大，概率越高）
        weights = {
            IllnessType.MILD_COLD: 30,           # 轻感冒 - 最常见
            IllnessType.HEADACHE: 20,            # 轻微头痛
            IllnessType.STIFF_NECK: 15,          # 落枕
            IllnessType.MINOR_SCRATCH: 15,       # 轻微擦伤
            IllnessType.NOSEBLEED: 10,           # 鼻血
            IllnessType.MOUTH_ULCER: 15,         # 口腔溃疡
            IllnessType.GASTROENTERITIS: 10,     # 肠胃炎
            IllnessType.SKIN_ALLERGY: 10,        # 皮肤过敏
            IllnessType.TONSILLITIS: 8,          # 扁桃体炎
            IllnessType.ANKLE_SPRAIN: 5,         # 脚踝扭伤
            IllnessType.SEVERE_COLD: 3,          # 重感冒 - 较少见
        }
        
        illness_types = []
        illness_weights = []
        
        for illness_type, weight in weights.items():
            illness_types.append(illness_type)
            illness_weights.append(weight)
        
        return random.choices(illness_types, weights=illness_weights, k=1)[0]
    
    def force_recovery(self):
        """强制康复"""
        if self.current_illness:
            logger.info(f"强制康复: {self.current_illness.illness_type.value}")
            self.recover_from_illness()
    
    def set_cool_down(self, cool_down_days: float):
        """设置冷却期"""
        self.cool_down_end_time = time.time() + (cool_down_days * 24 * 3600)
        logger.info(f"设置冷却期: {cool_down_days}天")
        self.save_state()
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        current_time = time.time()
        
        status = {
            "is_healthy": self.current_illness is None,
            "in_cool_down": current_time < self.cool_down_end_time,
            "current_illness": None,
            "cool_down_remaining": 0,
            "last_recovery_time": self.last_recovery_time
        }
        
        if status["in_cool_down"]:
            status["cool_down_remaining"] = (self.cool_down_end_time - current_time) / 3600
        
        if self.current_illness:
            illness = self.current_illness
            duration_hours = illness.get_duration_hours()
            expected_duration = get_illness_duration(illness.illness_type)
            remaining_hours = max(0, expected_duration - duration_hours)
            
            status["current_illness"] = {
                "type": illness.illness_type.value,
                "description": get_illness_description(illness.illness_type),
                "start_time": illness.start_time,
                "duration_hours": duration_hours,
                "remaining_hours": remaining_hours,
                "severity": illness.severity,
                "stage": illness.stage
            }
            
            if remaining_hours > 24:
                days = remaining_hours / 24
                status["recovery_remaining_hours"] = remaining_hours
                status["recovery_time_text"] = f"预计还有{days:.1f}天康复"
            else:
                status["recovery_remaining_hours"] = remaining_hours
                status["recovery_time_text"] = f"预计还有{remaining_hours:.1f}小时康复"
        
        return status
    
    def get_current_illness_description(self) -> Optional[str]:
        """获取当前疾病描述"""
        if self.current_illness:
            return get_illness_description(self.current_illness.illness_type)
        return None
    
    def get_illness_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取疾病历史记录"""
        try:
            history = self.storage.get("illness_history", [])
            return history[-limit:] if history else []
        except Exception as e:
            logger.error(f"获取疾病历史记录失败: {e}")
            return []