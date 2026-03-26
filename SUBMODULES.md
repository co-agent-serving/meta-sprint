# Git Submodules 管理指南

本文档说明 Serving Agent 项目中使用的 Git Submodules。

## Submodules 概览

### 必需依赖（✅ Phase 1-3）

| 路径 | 仓库 | 用途 | 优先级 |
|------|------|------|--------|
| `modules/pypto` | [hw-native-sys/pypto](https://github.com/hw-native-sys/pypto) | PyPTO 编程框架，IR 构建和代码生成 | P0 |
| `modules/simpler` | [hw-native-sys/simpler](https://github.com/hw-native-sys/simpler) | PTO 任务运行时，单机推理 | P0 |

### 可选依赖（⚠️ 推荐）

| 路径 | 仓库 | 用途 | 优先级 |
|------|------|------|--------|
| `modules/pypto-lib` | [hw-native-sys/pypto-lib](https://github.com/hw-native-sys/pypto-lib) | Tensor 操作库，模型实现 | P1 |
| `modules/pypto-serving` | [hengliao1972/pypto-serving](https://github.com/hengliao1972/pypto-serving) | 推理引擎参考架构 | P2 |

### 分布式依赖（✅ Phase 4）

| 路径 | 仓库 | 用途 | 优先级 |
|------|------|------|--------|
| `modules/pypto_runtime_distributed` | [hengliao1972/pypto_runtime_distributed](https://github.com/hengliao1972/pypto_runtime_distributed) | Linqu 分布式运行时，多机通信 | P1（Phase 4） |

### 间接依赖（❌ 透明）

| 路径 | 仓库 | 用途 | 优先级 |
|------|------|------|--------|
| `modules/pto-isa` | [PTO-ISA/pto-isa](https://github.com/PTO-ISA/pto-isa) | PTO 虚拟指令集，链接静态库 | P3 |
| `modules/PTOAS` | [zhangstevenunity/PTOAS](https://github.com/zhangstevenunity/PTOAS) | PTO 编译器，通过 pypto 调用 | P3 |

### 参考实现（📚 学习）

| 路径 | 仓库 | 用途 |
|------|------|------|
| `reference/rust_llm_server` | [xwhu/pypto_workspace](https://github.com/xwhu/pypto_workspace) | Rust LLM 服务器参考实现 |

## 快速开始

### 仅初始化必需模块（推荐）

```bash
# 克隆主仓库（不含 submodules）
git clone <repository-url> serving_agent
cd serving_agent

# 仅初始化 Phase 1-3 必需的模块
git submodule update --init modules/pypto modules/simpler

# 可选：添加 pypto-lib（复用 tensor 函数）
git submodule update --init modules/pypto-lib
```

### 初始化所有模块

```bash
# 克隆时递归初始化所有 submodules
git clone --recurse-submodules <repository-url> serving_agent

# 或者：如果已经克隆，初始化所有 submodules
git submodule update --init --recursive
```

### 选择性初始化（按阶段）

```bash
# Phase 1-2: 单机推理
git submodule update --init modules/pypto modules/simpler

# Phase 3: 使用 pypto-lib 组件
git submodule update --init modules/pypto-lib

# Phase 4: 多机分布式
git submodule update --init modules/pypto_runtime_distributed

# 参考实现（学习用）
git submodule update --init reference/rust_llm_server
```

## 常用操作

### 更新 Submodules

```bash
# 更新所有 submodules 到最新版本
git submodule update --remote --merge

# 更新特定 submodule
git submodule update --remote modules/pypto

# 查看 submodule 状态
git submodule status
```

### 在 Submodule 中工作

```bash
# 进入 submodule 目录
cd modules/pypto

# 切换到特定分支
git checkout dev-branch

# 在 submodule 中提交
git commit -am "Changes in pypto"

# 返回主仓库
cd ../..

# 更新 submodule 引用
git add modules/pypto
git commit -m "Update pypto submodule"
```

### 删除 Submodule

```bash
# 1. 删除 .gitmodules 中的配置
# 2. 删除 .git/config 中的配置
git config --remove-section submodule.modules/pypto

# 3. 删除缓存
git rm --cached modules/pypto

# 4. 删除目录
rm -rf modules/pypto
rm -rf .git/modules/modules/pypto
```

## 依赖关系图

```
serving_agent/
├── Phase 1-2 (单机)
│   ├── pypto          # ──┐
│   └── simpler        #   ├── 直接依赖
│                         │
├── Phase 3 (代码生成)     │
│   ├── pypto          # <┘
│   └── pypto-lib      # ─── 可选
│
├── Phase 4 (多机)
│   ├── pypto_runtime_distributed  # ──┐
│   ├── pypto          #               ├── 直接依赖
│   └── simpler        # ──────────────┘
│
└── 间接依赖（透明）
    ├── pto-isa        # 被 simpler 链接
    └── PTOAS          # 被 pypto 调用
```

## 开发工作流

### 设置开发环境

```bash
# 1. 克隆主仓库
git clone --recurse-submodules <repository-url> serving_agent
cd serving_agent

# 2. 检查 submodule 状态
git submodule status

# 3. 如果 submodule 未初始化
git submodule update --init --recursive

# 4. 安装 Python 依赖
pip install -e .
```

### 使用 PyPTO API

```python
# serving_agent/pypto_codegen/kernelgen.py
import sys
sys.path.insert(0, "modules/pypto")

from pypto import ir, compile

# 构建 IR
@ir.function
def my_kernel(x: ir.Tensor[(1024, 1024), ir.FP16]) -> ir.Tensor[(1024, 1024), ir.FP16]:
    return ir.matmul(x, x)

# 编译到 PTO
pto_code = compile.compile_to_pto(my_kernel, target="ascend910b")
```

### 版本兼容性

不同模块之间可能有版本依赖关系：

| 主模块版本 | pypto 版本 | simpler 版本 | pypto-lib 版本 |
|-----------|-----------|-------------|----------------|
| serving-agent 0.1 | pypto >= 0.5.0 | simpler >= 0.3.0 | pypto-lib >= 0.2.0 |

更新 submodule 前请检查兼容性。

## 故障排查

### Submodule 为空

```bash
# 检查 submodule 状态
git submodule status

# 如果看到 "-" 开头，表示未初始化
git submodule update --init --recursive
```

### Submodule 分离头指针

```bash
# 进入 submodule 目录
cd modules/pypto

# 查看当前状态
git status

# 如果显示 "detached HEAD"，切换到主分支
git checkout main
```

### Submodule 权限问题

某些仓库可能需要访问权限。请：
1. 确认你有对应仓库的访问权限
2. 配置 SSH 密钥或访问令牌
3. 使用 SSH URL 替代 HTTPS URL

## 最佳实践

1. **按需初始化**：只初始化当前阶段需要的 submodules
2. **锁定版本**：在 `.gitmodules` 中指定 `branch`，使用固定 commit
3. **文档化**：在每次更新 submodule 时更新 CHANGELOG.md
4. **测试兼容性**：更新 submodule 后运行完整测试套件
5. **定期同步**：定期检查 upstream 更新，评估是否需要合并

## 相关文档

- [Git Submodules 官方文档](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [PyPTO 模块分析](docs/modules_analysis_and_serving_agent_requirements.md)
- [实施计划](docs/serving_agent_implementation_plan.md)
