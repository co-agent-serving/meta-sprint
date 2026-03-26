# Serving Agent 快速开始指南

## 安装

```bash
# 克隆仓库
cd serving_agent

# 安装依赖
pip install -e .
```

## 配置示例

创建 `config.toml` 文件：

```toml
[model]
name = "qwen3"
variant = "8b"
weights_path = "/data/models/qwen3-8b"

[hardware]
backend_type = "pypto"
device_id = 0
npus_per_node = 8
nodes = 1

[backend]
codegen_level = "tile"
use_cache = true
optimize_for = "latency"

[parallel]
tensor_parallel_size = 1
pipeline_parallel_size = 1

[features]
kv_cache = "paged"
batching = "continuous"
quantization = "none"
```

## 使用命令

### 验证配置

```bash
serving-agent validate config.toml
```

### 生成推理服务

```bash
serving-agent generate config.toml --output ./my_server
```

### 构建项目

```bash
cd my_server
cargo build --release
```

## 项目结构

```
serving_agent/
├── serving_agent/        # 主包
│   ├── config/          # 配置解析和验证
│   ├── assembler/       # 项目组装器
│   ├── pypto_codegen/   # PyPTO 内核生成
│   └── cli.py           # 命令行接口
├── templates/           # Jinja2 模板
├── examples/            # 示例配置
├── tests/               # 测试
└── docs/                # 文档
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black serving_agent/
ruff check serving_agent/
```

## 下一步

- 阅读 [实施计划](docs/serving_agent_implementation_plan.md)
- 查看 [模块分析](docs/modules_analysis_and_serving_agent_requirements.md)
- 参考 [Rust 服务器分析](docs/rust_llm_server_analysis.md)
