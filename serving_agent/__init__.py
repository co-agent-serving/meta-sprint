"""
Serving Agent - 自动生成轻量级 LLM 推理服务框架

根据配置自动生成针对 Ascend NPU 优化的推理服务。
"""

__version__ = "0.1.0"
__author__ = "Serving Agent Team"

from serving_agent.config import ServingConfig, validate_config
from serving_agent.assembler import ProjectAssembler
from serving_agent.pypto_codegen import Qwen3KernelGenerator

__all__ = [
    "ServingConfig",
    "validate_config",
    "ProjectAssembler",
    "Qwen3KernelGenerator",
]
