# Serving Agent

根据配置自动生成轻量级 LLM 推理服务框架。

## 项目概述

**Serving Agent** 是一个代码生成工具，能够根据部署需求（硬件、模型等）自动生成轻量级的 LLM 推理服务框架。

### 核心特点

- **PyPTO 唯一后端**：统一的 Tile 级抽象，代码生成量 < 10000 行
- **目标硬件**：Ascend NPU (910B)
- **支持部署**：单机多卡、多机分布式
- **AI 友好**：代码量可控，便于 AI 理解和修改

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: 需求分析与规划                                     │
│  用户配置 (TOML/JSON) → 配置验证 → 部署计划生成               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: 代码生成与组装                                     │
│  模板引擎 → 组件选择 → 项目组装（Cargo.toml, build.rs）      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: 验证与部署                                         │
│  构建测试 → 集成验证 → 部署包生成                             │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
serving_agent/
├── config/              # 配置解析和验证
│   ├── __init__.py
│   ├── parser.py        # TOML/JSON 解析
│   └── validator.py     # 配置验证
├── templates/           # Jinja2 模板
│   ├── core/            # 核心服务器组件
│   ├── backends/        # 计算后端变体
│   ├── parallel/        # 并行策略
│   └── communication/   # 通信层
├── assembler/           # 项目组装器
│   ├── __init__.py
│   └── builder.py       # 组装 Rust 项目
├── pypto_codegen/       # PyPTO 内核生成器
│   ├── __init__.py
│   └── qwen3_kernelgen.py
├── cli.py               # 命令行接口
└── __init__.py
```

## 快速开始

### 安装依赖

```bash
# Python 依赖
pip install -e .

# Rust 依赖（生成的项目需要）
# Rust 1.70+
```

### 使用示例

```bash
# 生成推理服务
serving-agent generate --config config.toml --output ./my_server

# 验证配置
serving-agent validate --config config.toml

# 构建项目
serving-agent build --project ./my_server
```

### 配置示例

```toml
[model]
name = "qwen3"
variant = "8b"
weights_path = "/data/models/qwen3-8b"

[hardware]
backend_type = "pypto"
device_id = 0
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

## 技术依赖

### 必需依赖

- **Python** 3.9+
- **Rust** 1.70+
- **PyPTO** modules/pypto（唯一后端）

### 环境依赖

- **Ascend CANN** 7.0+
- **HCCL**（多卡需要）

## 相关仓库

| 模块 | 仓库 | 是否需要接口 |
|------|------|-------------|
| pypto | [hw-native-sys/pypto](https://github.com/hw-native-sys/pypto) | ✅ 必须 |
| simpler | [hw-native-sys/simpler](https://github.com/hw-native-sys/simpler) | ✅ 必须 |
| pypto_runtime_distributed | [hengliao1972/pypto_runtime_distributed](https://github.com/hengliao1972/pypto_runtime_distributed) | ✅ 必须 |
| pypto-lib | [hw-native-sys/pypto-lib](https://github.com/hw-native-sys/pypto-lib) | ⚠️ 可选 |

## 开发路线图

### Phase 1: PyPTO 后端基础（第 1-4 周）
- PyPTO Ascend 后端实现
- Qwen3-0.6B 推理验证

### Phase 2: 分布式通信基础（第 5-8 周）
- PyPTO 通信原语集成
- 单机多卡 TP 支持

### Phase 3: Serving Agent 原型（第 9-12 周）
- 配置解析器
- 模板引擎
- CLI 工具

### Phase 4: 多机分布式支持（第 13-16 周）
- 跨机器 Pipeline/Tensor Parallel
- TCP 通信层

### Phase 5: PyPTO 性能优化（第 17-20 周）
- 完整内核套件
- 性能基准测试

## 文档

详细文档请查看 `docs/` 目录：

- [README](docs/README.md) - 文档导航
- [实施计划](docs/serving_agent_implementation_plan.md) - 完整实施计划
- [模块分析](docs/modules_analysis_and_serving_agent_requirements.md) - 依赖模块分析
- [Rust 服务器分析](docs/rust_llm_server_analysis.md) - 参考实现分析

## 许可证

MIT License

## 联系方式

项目相关问题请在 Issue 中提出。
