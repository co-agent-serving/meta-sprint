# Serving Agent 设计文档

## 项目概览

**Serving Agent**：根据配置自动生成轻量级 LLM 推理服务

- 核心特点：PyPTO 唯一后端、代码生成量 < 10000 行
- 目标硬件：Ascend NPU
- 支持部署：单机多卡、多机分布式

## 文档列表

| 文档 | 说明 | 阅读目的 |
|------|------|------|
| **[实施计划](./serving_agent_implementation_plan.md)** | 项目架构、5 个阶段的实施路线图、交付物 | 了解项目全貌 |
| **[模块分析](./modules_analysis_and_serving_agent_requirements.md)** | 7 个核心模块功能分析、接口依赖、AI 友好性要求 | 集成各模块接口 |
| **[Rust 服务器分析](./rust_llm_server_analysis.md)** | rust_llm_server & rustBindings 技术深度解析 | 参考 Rust 实现 |

## 相关仓库

| 模块 | 仓库 | Serving Agent 是否需要接口 |
|------|------|---------------------------|
| pypto | [hw-native-sys/pypto](https://github.com/hw-native-sys/pypto) | ✅ 必须（IR 构建、代码生成） |
| simpler | [hw-native-sys/simpler](https://github.com/hw-native-sys/simpler) | ✅ 必须（单机运行时） |
| pypto_runtime_distributed | [hengliao1972/pypto_runtime_distributed](https://github.com/hengliao1972/pypto_runtime_distributed) | ✅ 必须（多机分布式） |
| pypto-lib | [hw-native-sys/pypto-lib](https://github.com/hw-native-sys/pypto-lib) | ⚠️ 可选（复用 tensor 函数） |
| pypto-serving | [hengliao1972/pypto-serving](https://github.com/hengliao1972/pypto-serving) | ⚠️ 参考架构 |
| pto-isa | [PTO-ISA/pto-isa](https://github.com/PTO-ISA/pto-isa) | ❌ 链接静态库 |
| PTOAS | [zhangstevenunity/PTOAS](https://github.com/zhangstevenunity/PTOAS) | ❌ 间接使用（通过 pypto）|

参考实现：[xwhu/pypto_workspace](https://github.com/xwhu/pypto_workspace)，其中 rustBindings 和 rust_llm_server 为使用Rust对接aclnn的首版serving实现，详见[Rust 服务器分析](./rust_llm_server_analysis.md)。