# Serving Agent 设计文档

## 文档导航

本文档目录帮助你快速找到所需信息。

### 📖 阅读顺序建议

```
新用户入门：
1. 项目概述 ← （当前文档）
2. project_vision.md     ← 了解为什么做这个项目
3. 主仓库 README.md      ← 快速开始使用

深入理解：
4. modules_analysis.md   ← 了解依赖模块和集成策略
5. rust_implementation.md ← 参考现有的 Rust 实现
```

---

## 📚 文档列表

| 文档 | 类型 | 阅读目的 |
|------|------|---------|
| **[项目愿景](./project_vision.md)** | 🎯 战略层 | 了解问题定义、预期效果、与 PyPTO 的协同关系 |
| **[模块分析](./modules_analysis.md)** | 🔧 技术层 | 了解 7 个核心模块功能、接口依赖、集成策略 |
| **[Rust 实现](./rust_implementation.md)** | 📚 参考资料 | rust_llm_server & rustBindings 技术深度解析 |

---

## 🎯 快速查找

### 我想了解...

| 需求 | 推荐文档 |
|------|---------|
| 为什么需要 Serving Agent？ | [project_vision.md - 第 1 节](./project_vision.md#1-问题陈述) |
| Serving Agent 和 PyPTO 的关系？ | [project_vision.md - 第 2.2 节](./project_vision.md#22-与-pypto-的协同关系) |
| 成功后是什么样子？ | [project_vision.md - 第 2.3 节](./project_vision.md#23-预期效果) |
| 需要哪些外部依赖？ | [project_vision.md - 第 5.2 节](./project_vision.md#52-外部能力诉求与协作边界) |
| 如何集成 PyPTO 等模块？ | [modules_analysis.md](./modules_analysis.md) |
| 参考的 Rust 实现？ | [rust_implementation.md](./rust_implementation.md) |

---

## 🔗 相关仓库

### 核心依赖（必须）

| 模块 | 仓库 | Serving Agent 使用方式 |
|------|------|----------------------|
| **pypto** | [hw-native-sys/pypto](https://github.com/hw-native-sys/pypto) | IR 构建、算子代码生成 |
| **simpler** | [hw-native-sys/simpler](https://github.com/hw-native-sys/simpler) | 单机运行时 API |
| **pypto_runtime_distributed** | [hengliao1972/pypto_runtime_distributed](https://github.com/hengliao1972/pypto_runtime_distributed) | 多机分布式通信 |

### 可选依赖

| 模块 | 仓库 | 说明 |
|------|------|------|
| **pypto-lib** | [hw-native-sys/pypto-lib](https://github.com/hw-native-sys/pypto-lib) | Tensor 函数库（可复用） |

### 参考实现

| 仓库 | 说明 |
|------|------|
| [xwhu/pypto_workspace](https://github.com/xwhu/pypto_workspace) | 包含 rustBindings 和 rust_llm_server 的首版实现 |

---

## 📝 文档维护

### 命名规范

采用 **描述型命名**（清晰优先）：
- `project_vision.md` - 项目愿景
- `modules_analysis.md` - 模块分析
- `rust_implementation.md` - Rust 实现分析

### 文档分类

- 🎯 **战略层**：project_vision.md - 为什么做、做成什么样
- 🔧 **技术层**：modules_analysis.md - 如何集成、接口设计
- 📚 **参考资料**：rust_implementation.md - 现有实现分析

### 添加新文档

1. 使用描述型命名（2-4 个词）
2. 在本文档中添加条目
3. 根据文档类型归入战略层/技术层/参考资料
4. 更新"快速查找"索引（如适用）

---

**最后更新**: 2026-03-26
