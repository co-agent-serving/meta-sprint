# co-agent-serving 项目管理

本仓库用于 **co-agent-serving** 组织的项目管理，包括技术文档和进展报告。

---

## 目录结构

```
├── docs/
│   ├── project_vision.md    # 项目愿景
│   ├── design/              # 技术设计文档
│   │   ├── rust_implementation.md
│   │   └── modules_analysis.md
│   └── report/              # 周报与进展报告
├── .github/                 # GitHub Issue 模板
├── .claude/                 # Claude Code 配置（skills、settings）
└── README.md
```

## 相关代码仓库

| 仓库 | 说明 |
|------|------|
| [hw-native-sys/pypto](https://github.com/hw-native-sys/pypto) | PyPTO 编程框架，IR 构建和算子代码生成 |
| [hw-native-sys/simpler](https://github.com/hw-native-sys/simpler) | PTO 任务运行时，单机推理 |
| [hw-native-sys/pypto-lib](https://github.com/hw-native-sys/pypto-lib) | PyPTO 标准库 |
| [hengliao1972/pypto_runtime_distributed](https://github.com/hengliao1972/pypto_runtime_distributed) | 分布式通信运行时 |
