from src.plugin_system.base.plugin_metadata import PluginMetadata
from .plugin import IllnessPlugin

# 定义插件元数据
__plugin_meta__ = PluginMetadata(
    name="生小病插件",
    description="一个模拟麦麦生病状态的插件，通过Prompt组件影响AI回复风格",
    usage="""
    使用方法：
    1. /health - 检查麦麦的健康状态
    2. /force_recovery - 强制康复（仅管理员）
    
    插件会根据配置的概率随机触发疾病，并通过Prompt影响AI的回复语气。
    支持多种疾病类型，每种疾病有不同的症状描述和持续时间。
    """,
    author="MoFox_Bot开发者",
    version="1.0.0",
    license="MIT",
    keywords=["生病", "健康", "状态", "Prompt", "语气"],
    categories=["娱乐", "功能"],
)