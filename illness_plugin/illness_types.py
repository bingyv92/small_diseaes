"""
疾病类型定义模块
定义了所有支持的疾病类型、症状描述和转换规则
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import time


class IllnessType(Enum):
    """疾病类型枚举"""
    SEVERE_COLD = "重感冒"
    MILD_COLD = "轻感冒"
    TONSILLITIS = "扁桃体炎/咽炎"
    GASTROENTERITIS = "肠胃不适(腹泻)"
    SKIN_ALLERGY = "皮肤过敏/皮疹"
    MINOR_SCRATCH = "轻微擦伤"
    HEADACHE = "轻微头痛"
    STIFF_NECK = "落枕"
    ANKLE_SPRAIN = "脚踝扭伤"
    NOSEBLEED = "鼻血"
    MOUTH_ULCER = "口腔溃疡"


@dataclass
class IllnessInfo:
    """疾病信息数据结构"""
    illness_type: IllnessType
    start_time: float
    severity: float = 0.5  # 严重程度 0-1
    stage: str = "initial"  # 阶段: initial, progressing, recovering
    
    def get_duration_hours(self) -> float:
        """获取已持续时间（小时）"""
        return (time.time() - self.start_time) / 3600


# 疾病症状描述映射
ILLNESS_DESCRIPTIONS = {
    IllnessType.SEVERE_COLD: "目前出现较为明显的上呼吸道感染症状，包括：鼻塞、咽部轻微疼痛、可能伴有低热（37.5-38℃）。建议适当休息，多补充水分。",
    IllnessType.MILD_COLD: "当前有轻微感冒症状，主要表现为：偶发喷嚏、鼻塞或轻微流涕，体温正常。保持充足睡眠即可。",
    IllnessType.TONSILLITIS: "咽部或扁桃体区域有轻微红肿，吞咽时可能出现轻微不适感。可尝试温盐水漱口，避免辛辣刺激食物。",
    IllnessType.GASTROENTERITIS: "胃肠道功能出现暂时性紊乱，表现为轻微腹痛或腹泻，每日排便次数略有增加。建议清淡饮食，避免生冷油腻。",
    IllnessType.SKIN_ALLERGY: "皮肤出现局部轻微红疹或小范围荨麻疹样改变，伴有轻度瘙痒。建议避免搔抓，穿着宽松棉质衣物。",
    IllnessType.MINOR_SCRATCH: "皮肤表层有轻微擦伤，范围较小，表皮略有破损，无活动性出血。保持局部清洁干燥即可。",
    IllnessType.HEADACHE: "头部出现轻微胀痛或钝痛感，部位不固定，程度不影响日常活动。可尝试闭目休息片刻。",
    IllnessType.STIFF_NECK: "颈部一侧肌肉有轻度紧张感，头部向某一方向转动时活动范围略受限，无明显疼痛。",
    IllnessType.ANKLE_SPRAIN: "踝关节活动时可能有轻微不适感，局部未见明显肿胀，行走功能基本正常。建议减少长时间站立。",
    IllnessType.NOSEBLEED: "鼻腔黏膜小血管破裂，单侧鼻孔有少量出血，通常在5分钟内可自行停止。建议保持头部前倾姿势。",
    IllnessType.MOUTH_ULCER: "口腔黏膜出现一处小型溃疡面，直径约2-3毫米，接触酸性或较硬食物时可能有轻微刺痛感。"
}


# 疾病持续时间和转换规则
ILLNESS_DURATION_HOURS = {
    IllnessType.SEVERE_COLD: 48,      # 2天
    IllnessType.MILD_COLD: 48,        # 2天
    IllnessType.TONSILLITIS: 48,      # 2天
    IllnessType.GASTROENTERITIS: 24,  # 1天
    IllnessType.SKIN_ALLERGY: 48,     # 2天
    IllnessType.MINOR_SCRATCH: 24,    # 1天
    IllnessType.HEADACHE: 24,         # 1天
    IllnessType.STIFF_NECK: 24,       # 1天
    IllnessType.ANKLE_SPRAIN: 48,     # 2天
    IllnessType.NOSEBLEED: 0.5,       # 30分钟（突发性）
    IllnessType.MOUTH_ULCER: 48,      # 2天
}


# 疾病转换规则：从当前疾病可能转换到的下一个疾病
ILLNESS_TRANSITIONS = {
    IllnessType.SEVERE_COLD: [IllnessType.MILD_COLD],  # 重感冒可能转为轻感冒
    IllnessType.MILD_COLD: [],  # 轻感冒直接康复
    IllnessType.TONSILLITIS: [],  # 扁桃体炎直接康复
    IllnessType.GASTROENTERITIS: [],  # 肠胃炎直接康复
    IllnessType.SKIN_ALLERGY: [],  # 皮肤过敏直接康复
    IllnessType.MINOR_SCRATCH: [],  # 轻微擦伤直接康复
    IllnessType.HEADACHE: [],  # 轻微头痛直接康复
    IllnessType.STIFF_NECK: [],  # 落枕直接康复
    IllnessType.ANKLE_SPRAIN: [],  # 脚踝扭伤直接康复
    IllnessType.NOSEBLEED: [],  # 鼻血直接康复
    IllnessType.MOUTH_ULCER: [],  # 口腔溃疡直接康复
}


# 疾病严重程度映射
ILLNESS_SEVERITY = {
    IllnessType.SEVERE_COLD: 0.8,
    IllnessType.MILD_COLD: 0.3,
    IllnessType.TONSILLITIS: 0.6,
    IllnessType.GASTROENTERITIS: 0.5,
    IllnessType.SKIN_ALLERGY: 0.4,
    IllnessType.MINOR_SCRATCH: 0.2,
    IllnessType.HEADACHE: 0.3,
    IllnessType.STIFF_NECK: 0.3,
    IllnessType.ANKLE_SPRAIN: 0.5,
    IllnessType.NOSEBLEED: 0.3,
    IllnessType.MOUTH_ULCER: 0.4,
}


def get_illness_description(illness_type: IllnessType) -> str:
    """获取疾病症状描述"""
    return ILLNESS_DESCRIPTIONS.get(illness_type, "身体不适，需要休息。")


def get_illness_duration(illness_type: IllnessType) -> float:
    """获取疾病持续时间（小时）"""
    return ILLNESS_DURATION_HOURS.get(illness_type, 24)


def get_illness_severity(illness_type: IllnessType) -> float:
    """获取疾病严重程度"""
    return ILLNESS_SEVERITY.get(illness_type, 0.5)


def get_possible_transitions(illness_type: IllnessType) -> List[IllnessType]:
    """获取可能的疾病转换"""
    return ILLNESS_TRANSITIONS.get(illness_type, [])


def get_all_illness_types() -> List[IllnessType]:
    """获取所有疾病类型"""
    return list(IllnessType)


def get_random_illness_type(exclude_types: Optional[List[IllnessType]] = None) -> IllnessType:
    """获取随机疾病类型（可排除指定类型）"""
    available_types = get_all_illness_types()
    
    if exclude_types:
        available_types = [t for t in available_types if t not in exclude_types]
    
    if not available_types:
        # 如果没有可用类型，返回轻感冒作为默认
        return IllnessType.MILD_COLD
    
    import random
    return random.choice(available_types)