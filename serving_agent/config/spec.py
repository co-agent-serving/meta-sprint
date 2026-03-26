"""
配置数据结构定义

定义 Serving Agent 的配置模型，使用 Pydantic 进行类型验证。
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ModelVariant(str, Enum):
    """支持的模型变体"""
    QWEN3_0_6B = "0.6b"
    QWEN3_4B = "4b"
    QWEN3_8B = "8b"


class BackendType(str, Enum):
    """后端类型"""
    PYPTO = "pypto"  # 唯一生产后端


class KVCacheType(str, Enum):
    """KV Cache 类型"""
    BASIC = "basic"
    PAGED = "paged"


class BatchingType(str, Enum):
    """批处理类型"""
    STATIC = "static"
    CONTINUOUS = "continuous"


class QuantizationType(str, Enum):
    """量化类型"""
    NONE = "none"
    INT8 = "int8"
    AWQ_INT4 = "awq-int4"


class CodegenLevel(str, Enum):
    """代码生成级别"""
    TILE = "tile"
    BLOCK = "block"
    OP = "op"


class OptimizeTarget(str, Enum):
    """优化目标"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"


class ModelConfig(BaseModel):
    """模型配置"""
    name: str = Field(..., description="模型名称，如 'qwen3'")
    variant: ModelVariant = Field(..., description="模型变体")
    weights_path: str = Field(..., description="模型权重文件路径")

    @field_validator("weights_path")
    @classmethod
    def validate_weights_path(cls, v: str) -> str:
        """验证权重路径"""
        import os
        if not os.path.exists(v):
            raise ValueError(f"Weights path does not exist: {v}")
        return v


class HardwareConfig(BaseModel):
    """硬件配置"""
    backend_type: BackendType = Field(default=BackendType.PYPTO, description="后端类型")
    device_id: int = Field(default=0, ge=0, le=7, description="NPU device ID")
    npus_per_node: int = Field(default=8, ge=1, le=8, description="每节点 NPU 数量")
    nodes: int = Field(default=1, ge=1, description="节点数量")


class BackendConfig(BaseModel):
    """后端配置"""
    codegen_level: CodegenLevel = Field(default=CodegenLevel.TILE, description="代码生成级别")
    use_cache: bool = Field(default=True, description="是否缓存编译内核")
    optimize_for: OptimizeTarget = Field(default=OptimizeTarget.LATENCY, description="优化目标")


class ParallelConfig(BaseModel):
    """并行配置"""
    tensor_parallel_size: int = Field(default=1, ge=1, description="Tensor Parallel 并行度")
    pipeline_parallel_size: int = Field(default=1, ge=1, description="Pipeline Parallel 并行度")

    @field_validator("tensor_parallel_size", "pipeline_parallel_size")
    @classmethod
    def validate_parallel_size(cls, v: int, info) -> int:
        """验证并行度是 2 的幂"""
        if v & (v - 1) != 0:
            raise ValueError(f"{info.field_name} must be a power of 2, got {v}")
        return v


class FeatureFlags(BaseModel):
    """功能开关"""
    kv_cache: KVCacheType = Field(default=KVCacheType.PAGED, description="KV Cache 类型")
    batching: BatchingType = Field(default=BatchingType.CONTINUOUS, description="批处理类型")
    quantization: QuantizationType = Field(
        default=QuantizationType.NONE, description="量化类型"
    )


class DistributedConfig(BaseModel):
    """分布式配置"""
    master_addr: str = Field(default="127.0.0.1", description="主节点地址")
    master_port: int = Field(default=29500, ge=1024, le=65535, description="主节点端口")
    communication: str = Field(default="pypto", description="通信后端")


class ServingConfig(BaseModel):
    """服务配置（根配置）"""
    model: ModelConfig
    hardware: HardwareConfig
    backend: BackendConfig = Field(default_factory=BackendConfig)
    parallel: ParallelConfig = Field(default_factory=ParallelConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    distributed: Optional[DistributedConfig] = Field(default=None, description="分布式配置")

    @field_validator("parallel")
    @classmethod
    def validate_total_devices(cls, v: ParallelConfig, info) -> ParallelConfig:
        """验证并行配置不超过可用设备"""
        # 从 hardware 获取总设备数（如果有的话）
        # 这里简化处理，实际应该从父级获取
        total_parallel = v.tensor_parallel_size * v.pipeline_parallel_size
        if total_parallel > 32:  # 合理上限
            raise ValueError(f"Total parallel degree {total_parallel} exceeds reasonable limit")
        return v
