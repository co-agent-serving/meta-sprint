"""
配置文件解析器

支持 TOML 和 JSON 格式的配置文件解析。
"""

from pathlib import Path
from typing import Union
import toml
import json

from serving_agent.config.spec import ServingConfig


def parse_config(config_path: Union[str, Path]) -> ServingConfig:
    """
    解析配置文件

    Args:
        config_path: 配置文件路径（.toml 或 .json）

    Returns:
        ServingConfig: 解析后的配置对象

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置文件格式不支持或解析失败
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    suffix = config_path.suffix.lower()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            if suffix == ".toml":
                data = toml.load(f)
            elif suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(
                    f"Unsupported config format: {suffix}. "
                    "Supported formats: .toml, .json"
                )

        # 使用 Pydantic 验证并解析
        config = ServingConfig(**data)
        return config

    except toml.TomlDecodeError as e:
        raise ValueError(f"Failed to parse TOML config: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON config: {e}")
