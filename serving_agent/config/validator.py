"""
配置验证器

验证配置的正确性和一致性，生成部署计划。
"""

from typing import List
from pathlib import Path

from serving_agent.config.spec import ServingConfig


class ConfigSpec:
    """
    配置规格

    经过验证的配置，包含部署计划所需的额外信息。
    """

    def __init__(
        self,
        config: ServingConfig,
        total_devices: int,
        layers_per_device: List[int],
    ):
        self.config = config
        self.total_devices = total_devices
        self.layers_per_device = layers_per_device

    @property
    def is_distributed(self) -> bool:
        """是否为分布式部署"""
        return self.config.hardware.nodes > 1

    @property
    def is_tensor_parallel(self) -> bool:
        """是否使用 Tensor Parallel"""
        return self.config.parallel.tensor_parallel_size > 1

    @property
    def is_pipeline_parallel(self) -> bool:
        """是否使用 Pipeline Parallel"""
        return self.config.parallel.pipeline_parallel_size > 1


def validate_config(config: ServingConfig) -> ConfigSpec:
    """
    验证配置并生成部署规格

    Args:
        config: 解析后的配置对象

    Returns:
        ConfigSpec: 验证后的配置规格

    Raises:
        ValueError: 配置验证失败
    """
    errors = []

    # 验证硬件配置
    total_npus = config.hardware.npus_per_node * config.hardware.nodes
    required_parallel = (
        config.parallel.tensor_parallel_size * config.parallel.pipeline_parallel_size
    )

    if required_parallel > total_npus:
        errors.append(
            f"Required parallel degree ({required_parallel}) "
            f"exceeds available NPUs ({total_npus})"
        )

    # 验证权重路径
    weights_path = Path(config.model.weights_path)
    if not weights_path.exists():
        errors.append(f"Weights path does not exist: {weights_path}")

    # 验证分布式配置
    if config.hardware.nodes > 1:
        if config.distributed is None:
            errors.append("Distributed config is required for multi-node deployment")

    # 如果有错误，抛出异常
    if errors:
        raise ValueError("Config validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    # 计算层分配（简化版，实际需要根据模型配置）
    # 这里假设 32 层均匀分配
    total_layers = 32  # 从模型配置获取
    layers_per_stage = total_layers // config.parallel.pipeline_parallel_size

    layers_per_device = []
    for stage_idx in range(config.parallel.pipeline_parallel_size):
        start_layer = stage_idx * layers_per_stage
        end_layer = start_layer + layers_per_stage if stage_idx < config.parallel.pipeline_parallel_size - 1 else total_layers
        layers_per_device.append(end_layer - start_layer)

    return ConfigSpec(
        config=config,
        total_devices=total_npus,
        layers_per_device=layers_per_device,
    )
