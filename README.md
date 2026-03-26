# Serving Agent

**配置驱动的 LLM 推理服务代码生成工具 —— PyPTO 应用闭环的完成者**

---

## 简介

Serving Agent 是一个配置驱动的代码生成工具，能够根据部署需求（硬件、模型、并行策略等）自动生成轻量级、可运行的 LLM 推理服务。

**核心特点**：
- 🚀 **配置驱动**：通过 TOML/JSON 配置生成服务，无需编写代码
- 🤖 **AI 友好**：目标代码量约 10000 行以内，结构清晰
- 🔧 **灵活组装**：支持多种并行策略（TP、PP、TP+PP）和部署场景
- ⚡ **PyPTO 原生**：深度集成 PyPTO 算子，充分发挥其性能优势

> 💡 **详细说明**：查看 [项目愿景](docs/vision.md) 了解问题定义、预期效果和与 PyPTO 的协同关系

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-org/serving-agent.git
cd serving-agent

# 安装 Python 依赖
pip install -e .
```

### 使用

```bash
# 1. 验证配置
$ serving-agent validate --config config.toml

# 2. 生成推理服务
$ serving-agent generate --config config.toml --output ./my_server

# 3. 构建项目
$ serving-agent build --project ./my_server
```

### 配置示例

```toml
[model]
name = "qwen3"
variant = "8b"
weights_path = "/data/models/qwen3-8b"

[hardware]
backend_type = "pypto"
npus_per_node = 8
nodes = 2

[parallel]
tensor_parallel_size = 4
pipeline_parallel_size = 2

[features]
kv_cache = "paged"
batching = "continuous"
quantization = "none"
```

---

## 技术依赖

### 核心依赖

| 依赖 | 说明 | 用途 |
|------|------|------|
| **PyPTO** | Tile 级算子生成 | 生成高性能 Ascend 内核 |
| **simpler** | 运行时 API | 设备管理、内存分配 |
| **pypto_runtime_distributed** | 分布式通信 | 单机多卡、多机通信 |
| **Ascend CANN** 7.0+ | NPU 驱动 | 硬件抽象 |

### 开发环境

- **Python** 3.9+（代码生成）
- **Rust** 1.70+（生成的服务）
- **Ascend NPU** 910B（目标硬件）

---

## 项目结构

```
serving_agent/
├── config/              # 配置解析和验证
│   ├── parser.py        # TOML/JSON 解析
│   └── validator.py     # 配置验证
├── templates/           # Jinja2 代码生成模板
│   ├── core/            # 核心服务组件
│   ├── backends/        # 计算后端（PyPTO）
│   ├── parallel/        # 并行策略（TP/PP）
│   └── communication/   # 通信层（单机/多机）
├── assembler/           # 项目组装器
│   └── builder.py       # 组装 Rust 项目
├── pypto_codegen/       # PyPTO 内核生成接口
└── cli.py               # 命令行工具
```

---

## 相关仓库

| 仓库 | 关系 | 说明 |
|------|------|------|
| [hw-native-sys/pypto](https://github.com/hw-native-sys/pypto) | 🔴 **必须** | PyPTO 核心，算子生成 |
| [hw-native-sys/simpler](https://github.com/hw-native-sys/simpler) | 🔴 **必须** | 运行时 API |
| [hengliao1972/pypto_runtime_distributed](https://github.com/hengliao1972/pypto_runtime_distributed) | 🔴 **必须** | 分布式通信 |
| [hw-native-sys/pypto-lib](https://github.com/hw-native-sys/pypto-lib) | 🟡 可选 | PyPTO 标准库 |

---

## 文档

- [项目愿景](docs/project_vision.md) - 问题定义、预期效果、与 PyPTO 的协同关系
- [模块分析](docs/modules_analysis.md) - 依赖模块分析
- [Rust 实现](docs/rust_implementation.md) - Rust 服务器参考实现
- [文档导航](docs/README.md) - 查看所有设计文档

---

## 许可证

Apache License 2.0

---

## 联系方式

项目相关问题请在 [Issue](https://github.com/your-org/serving-agent/issues) 中提出。
