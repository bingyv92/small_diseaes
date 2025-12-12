"""
生小病插件主模块
包含插件主类、Prompt组件、事件处理器和命令组件
"""

import time
from typing import List, Tuple, Type, Optional
from src.plugin_system import (
    BasePlugin, register_plugin, ComponentInfo, ConfigField,
    BasePrompt, PlusCommand, CommandArgs, ChatType,
    BaseEventHandler, EventType
)
from src.plugin_system.base.component_types import InjectionRule, InjectionType
from src.plugin_system.base.base_event import HandlerResult
from src.chat.utils.prompt_params import PromptParameters
from src.plugin_system.apis import storage_api, get_logger
from src.chat.utils.prompt_params import PromptParameters
from .illness_manager import IllnessManager

logger = get_logger("illness_plugin")

# 获取插件的本地存储实例
plugin_storage = storage_api.get_local_storage("illness_plugin")


# ==================== Prompt组件 ====================

class IllnessPrompt(BasePrompt):
    """根据疾病状态生成提示词的组件"""
    
    prompt_name = "illness_prompt"
    prompt_description = "根据麦麦当前的生病状态调整回复风格和语气"
    
    injection_point = ["s4u_style_prompt", "normal_style_prompt", "kfc_main", "kfc_replyer", "afc_main", "afc_replyer"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.illness_manager = IllnessManager(plugin_storage)
    
    async def execute(self) -> str:
        """生成提示词 - 增强KFC/AFC模式支持"""
        verbose = self.get_config("verbose_logging", False)
        target_prompt = getattr(self, 'target_prompt_name', None)
        logger.info(f"[IllnessPrompt] 执行提示词生成，目标Prompt: {target_prompt}, verbose={verbose}")
        if verbose:
            logger.debug(f"[IllnessPrompt] 执行提示词生成，目标Prompt: {target_prompt}")
        
        if not self.illness_manager:
            logger.info("[IllnessPrompt] 疾病管理器未设置，跳过")
            if verbose:
                logger.debug("[IllnessPrompt] 疾病管理器未设置，跳过")
            return ""
        
        illness_desc = self.illness_manager.get_current_illness_description()
        
        if not illness_desc:
            logger.info("[IllnessPrompt] 无疾病描述，跳过")
            if verbose:
                logger.debug("[IllnessPrompt] 无疾病描述，跳过")
            return ""
        
        # 根据疾病类型调整语气
        illness_type = self.illness_manager.current_illness.illness_type
        
        # 获取配置
        kfc_enabled = self.get_config("kfc_integration.enabled", True)
        kfc_mode = self.get_config("kfc_integration.mode", "unified")
        
        # 检测当前聊天模式
        is_kfc_mode = False
        is_afc_mode = False
        
        if target_prompt:
            target_name = target_prompt.lower()
            if any(kfc_key in target_name for kfc_key in ['kfc', 'kokoro', 'flow', 'chatter', '私聊', '心流']):
                is_kfc_mode = True
            elif any(afc_key in target_name for afc_key in ['afc', 'group', '群聊', 'normal']):
                is_afc_mode = True
        
        if verbose:
            logger.debug(f"[IllnessPrompt] 疾病描述: {illness_desc}, 类型: {illness_type.value}, KFC模式: {is_kfc_mode}, AFC模式: {is_afc_mode}")
        
        # 根据聊天模式生成不同的提示词
        if kfc_enabled and is_kfc_mode:
            prompt = self._generate_kfc_prompt(illness_type, illness_desc, kfc_mode)
        elif is_afc_mode:
            prompt = self._generate_afc_prompt(illness_type, illness_desc)
        else:
            prompt = self._generate_normal_prompt(illness_type, illness_desc)
        
        if verbose:
            logger.debug(f"[IllnessPrompt] 生成的提示词: {prompt[:100]}...")
        
        logger.info(f"[IllnessPrompt] 疾病提示词已生成（疾病: {illness_type.value}, 目标: {target_prompt}）")
        return prompt
    
    def _generate_normal_prompt(self, illness_type, illness_desc: str) -> str:
        """生成普通模式提示词"""
        # 定义不同疾病对应的语气调整
        tone_adjustments = {
            "重感冒": "因为重感冒，声音有些沙哑，说话比较慢，需要经常停下来咳嗽或擤鼻涕。",
            "轻感冒": "因为轻感冒，鼻子有点塞，偶尔会打喷嚏，声音听起来有点闷闷的。",
            "扁桃体炎/咽炎": "因为咽喉炎，吞咽时会有点痛，说话声音比较轻，需要时不时喝水润喉。",
            "肠胃不适(腹泻)": "因为肠胃不适，说话时会偶尔停顿，声音听起来有点虚弱。",
            "皮肤过敏/皮疹": "因为皮肤过敏，感觉有些不适，语气中带着一点点烦躁。",
            "轻微擦伤": "因为轻微擦伤，行动有些不便，但精神状态还不错。",
            "轻微头痛": "因为轻微头痛，思考速度会慢一些，说话声音比较轻。",
            "落枕": "因为落枕，颈部活动受限，转头时会有些不适。",
            "脚踝扭伤": "因为脚踝扭伤，走路有些不便，需要坐着休息。",
            "鼻血": "刚刚止住鼻血，说话时还会用纸巾轻轻按着鼻子。",
            "口腔溃疡": "因为口腔溃疡，说话时会尽量避免碰到溃疡处，发音有些不清。",
        }
        
        base_tone = tone_adjustments.get(illness_type.value, "因为身体不适，精神不是很好，说话比较轻声细语。")
        
        prompt = f"""
请注意：麦麦目前生病了，具体症状是：{illness_desc}

回复时需要体现以下特点：
1. {base_tone}
2. 回复内容可以稍微简短一些，因为精力有限
3. 可以适当地表达需要休息的意愿
4. 对于复杂的问题可能需要更多时间思考
5. 语气要温和、耐心，但略带疲惫

记住：这只是模拟生病状态，麦麦的核心人格和知识不受影响。
"""
        
        return prompt.strip()
    
    def _generate_kfc_prompt(self, illness_type, illness_desc: str, kfc_mode: str) -> str:
        """生成KFC模式提示词"""
        # KFC模式下更自然简洁的描述
        kfc_tone_adjustments = {
            "重感冒": "今天重感冒，声音沙哑，说话慢，会咳嗽",
            "轻感冒": "今天有点感冒，鼻子不通，偶尔打喷嚏",
            "扁桃体炎/咽炎": "今天喉咙痛，说话轻声，需要喝水",
            "肠胃不适(腹泻)": "今天肚子不舒服，说话有气无力",
            "皮肤过敏/皮疹": "今天皮肤过敏，有点烦躁，不太舒服",
            "轻微擦伤": "今天有点小擦伤，行动不太方便",
            "轻微头痛": "今天头有点痛，思考慢，声音轻",
            "落枕": "今天落枕了，脖子不太能动",
            "脚踝扭伤": "今天脚踝扭了，走路不太方便",
            "鼻血": "刚刚流鼻血，说话还会按着鼻子",
            "口腔溃疡": "今天口腔溃疡，说话不太清楚",
        }
        
        kfc_tone = kfc_tone_adjustments.get(illness_type.value, "今天身体不太舒服，精神不太好")
        
        if kfc_mode == "unified":
            prompt = f"""
你当前生病了：{illness_desc}
{kfc_tone}，需要多休息。
回复简短些，语气温和但疲惫，可以表达需要休息。
记住这只是模拟状态，核心人格不变。
"""
        else:
            prompt = f"""
【身体状态】{kfc_tone}
【症状描述】{illness_desc}
【当前需求】需要休息，回复简短
【语气要求】温和耐心，略带疲惫
"""
        
        return prompt.strip()
    
    def _generate_afc_prompt(self, illness_type, illness_desc: str) -> str:
        """生成AFC模式提示词"""
        # AFC模式下更正式一些的描述
        afc_tone_adjustments = {
            "重感冒": "因重感冒导致声音沙哑、语速缓慢，伴有咳嗽",
            "轻感冒": "因轻感冒出现鼻塞、偶尔打喷嚏，声音略显沉闷",
            "扁桃体炎/咽炎": "因咽喉炎导致吞咽不适，说话声音较轻",
            "肠胃不适(腹泻)": "因肠胃不适导致说话时有气无力",
            "皮肤过敏/皮疹": "因皮肤过敏感到不适，语气略显烦躁",
            "轻微擦伤": "因轻微擦伤导致行动稍有不便",
            "轻微头痛": "因轻微头痛导致思考缓慢，声音较轻",
            "落枕": "因落枕导致颈部活动受限",
            "脚踝扭伤": "因脚踝扭伤导致行走不便",
            "鼻血": "因鼻血刚止，说话时仍需轻按鼻部",
            "口腔溃疡": "因口腔溃疡导致发音不清",
        }
        
        afc_tone = afc_tone_adjustments.get(illness_type.value, "因身体不适导致精神状态不佳")
        
        prompt = f"""
请注意：麦麦目前生病了。
症状：{illness_desc}
表现：{afc_tone}

回复要求：
1. 内容可适当简短，体现精力有限
2. 可表达需要休息的意愿
3. 对复杂问题可能需要更多思考时间
4. 保持温和耐心的语气

此为模拟生病状态，核心功能不受影响。
"""
        
        return prompt.strip()


# ==================== 事件处理器 ====================

class IllnessStateHandler(BaseEventHandler):
    """处理疾病状态更新的事件处理器"""
    
    handler_name = "illness_state_handler"
    handler_description = "定期更新疾病状态并检查是否触发新疾病"
    init_subscribe = [EventType.ON_START]
    weight = 10  # 较高优先级
    
    def __init__(self):
        super().__init__()
        self.illness_manager = None
        self.config = None
    
    def set_components(self, manager: IllnessManager, config: dict):
        """设置依赖组件"""
        self.illness_manager = manager
        self.config = config
    
    async def execute(self, params: dict) -> HandlerResult:
        """执行状态更新"""
        try:
            if not self.illness_manager or not self.config:
                return HandlerResult(success=True, continue_process=True)
            
            # 更新现有疾病状态
            self.illness_manager.update_illness_state()
            
            # 检查是否应该生病
            daily_probability = self.config.get("daily_probability", 0.05)
            if self.illness_manager.should_get_sick(daily_probability):
                new_illness = self.illness_manager.trigger_random_illness()
                if new_illness:
                    logger.info(f"触发新疾病：{new_illness.illness_type.value}")
            
            return HandlerResult(
                success=True,
                continue_process=True,
                message="疾病状态更新完成"
            )
            
        except Exception as e:
            logger.error(f"疾病状态更新失败：{e}")
            return HandlerResult(
                success=False,
                continue_process=True,
                message=f"疾病状态更新失败：{str(e)}"
            )


# ==================== 命令组件 ====================

class HealthCheckCommand(PlusCommand):
    """检查健康状态的命令"""
    
    command_name = "health"
    command_description = "检查麦麦的健康状态"
    command_aliases = ["健康", "身体状态", "生病"]
    chat_type_allow = ChatType.ALL
    
    # 类级别的疾病管理器引用
    _illness_manager = None
    
    @classmethod
    def set_illness_manager(cls, manager: IllnessManager):
        cls._illness_manager = manager
    
    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        if not self.__class__._illness_manager:
            await self.send_text("健康系统未初始化")
            return False, "系统未初始化", True
        
        status = self.__class__._illness_manager.get_health_status()
        
        if status["is_healthy"]:
            if status["in_cool_down"]:
                remaining_hours = status["cool_down_remaining"]
                if remaining_hours > 24:
                    days = remaining_hours / 24
                    message = f"✅ 麦麦目前很健康！\n\n刚刚康复不久，正在休息恢复中，还有{days:.1f}天的恢复期。"
                else:
                    message = f"✅ 麦麦目前很健康！\n\n刚刚康复不久，正在休息恢复中，还有{remaining_hours:.1f}小时的恢复期。"
            else:
                message = "✅ 麦麦目前非常健康，精力充沛！"
        else:
            illness_info = status["current_illness"]
            illness_type = illness_info["type"]
            description = illness_info["description"]
            
            if "recovery_remaining_hours" in status:
                remaining = status["recovery_remaining_hours"]
                if remaining > 24:
                    days = remaining / 24
                    recovery_time = f"预计还有{days:.1f}天康复"
                else:
                    recovery_time = f"预计还有{remaining:.1f}小时康复"
            else:
                recovery_time = "突发性症状，很快就会恢复"
            
            message = f"🤒 麦麦目前生病了\n\n" \
                     f"**疾病类型**: {illness_type}\n" \
                     f"**症状描述**: {description}\n" \
                     f"**恢复时间**: {recovery_time}\n\n" \
                     f"请对麦麦温柔一些哦～"
        
        await self.send_text(message)
        return True, "健康状态查询成功", True


class ForceRecoveryCommand(PlusCommand):
    """强制康复命令（仅Master可用）"""
    
    command_name = "force_recovery"
    command_description = "强制麦麦恢复健康（仅管理员）"
    command_aliases = ["康复", "恢复健康"]
    chat_type_allow = ChatType.PRIVATE  # 仅私聊可用
    
    # 类级别的疾病管理器引用
    _illness_manager = None
    
    @classmethod
    def set_illness_manager(cls, manager: IllnessManager):
        cls._illness_manager = manager
    
    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        if not self.__class__._illness_manager:
            await self.send_text("健康系统未初始化")
            return False, "系统未初始化", True
        
        # 检查是否是Master（这里需要权限系统，先简化处理）
        # 在实际应用中应该使用权限装饰器 @require_master
        
        cool_down_days = self.get_config("recovery.cool_down_days", 3.0)
        
        self.__class__._illness_manager.force_recovery()
        self.__class__._illness_manager.set_cool_down(cool_down_days)
        
        await self.send_text("✅ 已强制麦麦恢复健康，并开始休息恢复期。")
        return True, "强制康复成功", True


class ForceSickCommand(PlusCommand):
    """强制生病命令（仅Master可用）"""
    
    command_name = "force_sick"
    command_description = "强制麦麦生病（仅管理员）"
    command_aliases = ["生病", "强制生病"]
    chat_type_allow = ChatType.PRIVATE  # 仅私聊可用
    
    # 类级别的疾病管理器引用
    _illness_manager = None
    
    @classmethod
    def set_illness_manager(cls, manager: IllnessManager):
        cls._illness_manager = manager
    
    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        if not self.__class__._illness_manager:
            await self.send_text("健康系统未初始化")
            return False, "系统未初始化", True
        
        # 检查是否是Master（这里需要权限系统，先简化处理）
        # 在实际应用中应该使用权限装饰器 @require_master
        
        # 触发随机疾病
        new_illness = self.__class__._illness_manager.trigger_random_illness()
        
        if new_illness:
            illness_type = new_illness.illness_type.value
            description = self.__class__._illness_manager.get_current_illness_description()
            await self.send_text(f"✅ 已强制麦麦生病\n\n**疾病类型**: {illness_type}\n**症状描述**: {description}\n\n请对麦麦温柔一些哦～")
            return True, "强制生病成功", True
        else:
            await self.send_text("❌ 触发疾病失败，请检查日志")
            return False, "触发疾病失败", True


# ==================== 主插件类 ====================

@register_plugin
class IllnessPlugin(BasePlugin):
    """生小病插件主类"""
    
    plugin_name = "illness_plugin"
    enable_plugin = True
    dependencies = []
    python_dependencies = []
    config_file_name = "config.toml"
    
    config_section_descriptions = {
        "general": "插件总开关配置",
        "probability": "生病概率相关配置",
        "recovery": "恢复相关配置",
        "features": "功能开关配置",
        "kfc_integration": "KFC/AFC模式集成配置"
    }
    
    config_schema = {
        "general": {
            "enable_plugin": ConfigField(
                type=bool,
                default=True,
                description="是否启用生小病插件",
                example="true"
            ),
        },
        "probability": {
            "daily_probability": ConfigField(
                type=float,
                default=0.05,
                description="每天生病的概率（0-1之间的小数），例如0.05表示5%的概率",
                example="0.05"
            ),
        },
        "recovery": {
            "cool_down_days": ConfigField(
                type=float,
                default=3.0,
                description="康复后的冷却时间（天），这段时间内不会再生病",
                example="3.0"
            ),
            "enable_auto_recovery": ConfigField(
                type=bool,
                default=True,
                description="是否启用自动康复功能"
            ),
        },
        "features": {
            "enable_health_check": ConfigField(
                type=bool,
                default=True,
                description="是否启用 /health 健康检查命令"
            ),
            "enable_force_recovery": ConfigField(
                type=bool,
                default=True,
                description="是否启用 /force_recovery 强制康复命令（仅管理员）"
            ),
            "enable_force_sick": ConfigField(
                type=bool,
                default=True,
                description="是否启用 /force_sick 强制生病命令（仅管理员）"
            ),
            "verbose_logging": ConfigField(
                type=bool,
                default=False,
                description="是否启用详细日志记录"
            )
        },
        "kfc_integration": {
            "enabled": ConfigField(
                type=bool,
                default=True,
                description="是否启用KFC（私聊模式）集成"
            ),
            "mode": ConfigField(
                type=str,
                default="unified",
                description="KFC工作模式: unified(统一模式) 或 split(分离模式)",
                example="unified"
            ),
            "priority": ConfigField(
                type=int,
                default=100,
                description="KFC模式下提示词注入的优先级"
            )
        }
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.illness_manager = None
        self.illness_prompt = None
        self.state_handler = None
        
    def initialize_components(self):
        """初始化组件依赖"""
        # 检查插件是否启用
        if not self.get_config("general.enable_plugin", True):
            logger.info("生小病插件已被禁用")
            return
        
        # 获取本地存储
        storage = storage_api.get_local_storage(self.plugin_name)
        
        # 初始化疾病管理器
        self.illness_manager = IllnessManager(storage)
        
        # 更新疾病状态（考虑离线时间）
        self.illness_manager.update_illness_state()
        
        # 获取配置
        config = {
            "daily_probability": self.get_config("probability.daily_probability", 0.05),
            "cool_down_days": self.get_config("recovery.cool_down_days", 3.0),
            "enable_auto_recovery": self.get_config("recovery.enable_auto_recovery", True),
            "verbose_logging": self.get_config("features.verbose_logging", False),
            "kfc_enabled": self.get_config("kfc_integration.enabled", True),
            "kfc_mode": self.get_config("kfc_integration.mode", "unified"),
            "kfc_priority": self.get_config("kfc_integration.priority", 100)
        }
        
        # 初始化事件处理器
        self.state_handler = IllnessStateHandler()
        self.state_handler.set_components(self.illness_manager, config)
        
        # 设置命令组件的疾病管理器
        HealthCheckCommand.set_illness_manager(self.illness_manager)
        ForceRecoveryCommand.set_illness_manager(self.illness_manager)
        ForceSickCommand.set_illness_manager(self.illness_manager)
        
        # 命令组件将在运行时由系统初始化，这里只需要创建类实例
        # 实际的命令实例会在消息到达时由系统创建
        
        logger.info(f"生小病插件初始化完成，当前状态：{self.illness_manager.get_health_status()}")
    
    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """注册插件的所有功能组件"""
        # 检查插件是否启用
        if not self.get_config("general.enable_plugin", True):
            logger.info("生小病插件已被禁用，不注册任何组件")
            return []
        
        self.initialize_components()
        
        components = []
        
        # 注册Prompt组件
        logger.info("[IllnessPlugin] 注册Prompt组件: illness_prompt")
        components.append((
            IllnessPrompt.get_prompt_info(),
            IllnessPrompt
        ))
        
        # 注册事件处理器
        if self.state_handler:
            components.append((
                self.state_handler.get_handler_info(),
                type(self.state_handler)
            ))
        
        # 根据配置注册命令
        if self.get_config("features.enable_health_check", True):
            components.append((
                HealthCheckCommand.get_plus_command_info(),
                HealthCheckCommand
            ))
        
        if self.get_config("features.enable_force_recovery", True):
            components.append((
                ForceRecoveryCommand.get_plus_command_info(),
                ForceRecoveryCommand
            ))
        
        if self.get_config("features.enable_force_sick", True):
            components.append((
                ForceSickCommand.get_plus_command_info(),
                ForceSickCommand
            ))
        
        return components
    
    async def on_plugin_loaded(self):
        """插件加载完成后的钩子"""
        logger.info(f"生小病插件加载完成！当前健康状态：")
        
        status = self.illness_manager.get_health_status()
        if status["is_healthy"]:
            if status["in_cool_down"]:
                logger.info(f"  状态：健康（恢复期中）")
                logger.info(f"  剩余恢复时间：{status['cool_down_remaining']:.1f}小时")
            else:
                logger.info(f"  状态：完全健康")
        else:
            illness_info = status["current_illness"]
            logger.info(f"  状态：生病中")
            logger.info(f"  疾病类型：{illness_info['type']}")
            logger.info(f"  发病时间：{time.strftime('%Y-%m-%d %H:%M', time.localtime(illness_info['start_time']))}")