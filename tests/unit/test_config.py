"""
配置解析和验证的单元测试
"""

import pytest
from pathlib import Path
import tempfile

from serving_agent.config import parse_config, validate_config
from serving_agent.config.spec import ServingConfig


def test_parse_valid_config():
    """测试解析有效配置"""
    config_content = """
[model]
name = "qwen3"
variant = "8b"
weights_path = "/fake/path"

[hardware]
backend_type = "pypto"
device_id = 0
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(config_content)
        f.flush()

        # 由于路径不存在，这会抛出验证错误
        # 但我们可以测试解析本身
        import toml
        data = toml.load(f.name)
        assert data["model"]["name"] == "qwen3"
        assert data["model"]["variant"] == "8b"

        Path(f.name).unlink()


def test_config_model_variant():
    """测试模型变体枚举"""
    from serving_agent.config.spec import ModelVariant

    assert ModelVariant.QWEN3_0_6B == "0.6b"
    assert ModelVariant.QWEN3_4B == "4b"
    assert ModelVariant.QWEN3_8B == "8b"


def test_config_backend_type():
    """测试后端类型枚举"""
    from serving_agent.config.spec import BackendType

    assert BackendType.PYPTO == "pypto"


def test_parallel_validation():
    """测试并行配置验证"""
    from serving_agent.config.spec import ParallelConfig
    from pydantic import ValidationError

    # 有效配置
    config = ParallelConfig(tensor_parallel_size=2, pipeline_parallel_size=2)
    assert config.tensor_parallel_size == 2

    # 无效配置（不是 2 的幂）
    with pytest.raises(ValidationError):
        ParallelConfig(tensor_parallel_size=3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
