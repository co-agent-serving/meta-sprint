# PyPTO 模块功能分析与 Serving Agent 集成需求

## 文档概述

本文档分析 `modules/` 目录下所有代码仓库的功能定位，评估 Serving Agent 对各模块接口的依赖需求，并从 **AI 理解友好性**和**开发友好性**角度提出接口设计要求。

**文档版本**: v1.0
**最后更新**: 2026-03-25
**分析范围**: PyPTO Workspace modules/ 下的 7 个核心模块

---

## 目录

1. [模块总览](#模块总览)
2. [详细分析](#详细分析)
3. [Serving Agent 集成策略](#serving-agent-集成策略)
4. [接口设计要求](#接口设计要求)
5. [优先级路线图](#优先级路线图)

---

## 模块总览

### 模块依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                      Serving Agent                          │
│                  (本文档分析对象)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌──────────────┐  ┌─────────────────────┐
│ pypto-serving │  │  pypto-lib   │  │      pypto          │
│   (推理引擎)  │  │ (Tensor 库)  │  │  (编程框架)         │
└───────┬───────┘  └──────┬───────┘  └──────────┬──────────┘
        │                 │                     │
        │                 │                     │
        ▼                 ▼                     ▼
┌───────────────┐  ┌──────────────┐  ┌─────────────────────┐
│    simpler    │  │  pypto-runtime│  │       PTOAS         │
│   (运行时)    │  │  _distributed│  │   (编译器)          │
└───────┬───────┘  └──────────────┘  └──────────┬──────────┘
        │                                      │
        │                                      │
        ▼                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      pto-isa                                │
│                  (指令集架构)                               │
└─────────────────────────────────────────────────────────────┘
```

### 模块分类

| 类别 | 模块 | 核心定位 | 仓库 |
|------|------|---------|------|
| **应用层** | pypto-serving | 高性能推理引擎（类似 vllm/sglang） | [hengliao1972/pypto-serving](https://github.com/hengliao1972/pypto-serving) |
| **库层** | pypto-lib | Tensor 操作库 + 模型实现 | [hw-native-sys/pypto-lib](https://github.com/hw-native-sys/pypto-lib) |
| **框架层** | pypto | AI 加速器编程框架（多级 IR） | [hw-native-sys/pypto](https://github.com/hw-native-sys/pypto) |
| **运行时层** | simpler | PTO 任务运行时（L0-L2） | [hw-native-sys/simpler](https://github.com/hw-native-sys/simpler) |
| **运行时层** | pypto_runtime_distributed | 分布式运行时（L3-L6） | [hengliao1972/pypto_runtime_distributed](https://github.com/hengliao1972/pypto_runtime_distributed) |
| **编译器层** | PTOAS | PTO Bytecode 编译器（MLIR） | [zhangstevenunity/PTOAS](https://github.com/zhangstevenunity/PTOAS) |
| **ISA 层** | pto-isa | PTO 虚拟指令集实现（C++ 库） | [PTO-ISA/pto-isa](https://github.com/PTO-ISA/pto-isa) |

---

## 详细分析

### 1. PTOAS (PTO Assembler & Optimizer)

**仓库**: [zhangstevenunity/PTOAS](https://github.com/zhangstevenunity/PTOAS)

#### 功能定位

**基于 MLIR 的 PTO Bytecode 编译器**，连接上层 AI 框架与底层硬件。

- **输入**: `.pto` 字节码文件（PTO Dialect）
- **输出**: C++ 代码（调用 pto-isa 库）或 EmitC/Linalg Dialect
- **核心职责**:
  1. IR 解析与验证（PTO Dialect Ops 语义）
  2. 达芬奇架构特定优化 Pass（算子融合、同步插入）
  3. 代码下降（PTO → EmitC/Linalg）
  4. Python 绑定（Pybind11）

#### 技术栈

- **依赖**: LLVM/MLIR 19.1.7（严格版本锁定）
- **语言**: C++ (实现) + Python (绑定)
- **输出**: 命令行工具 `ptoas`，Python 模块 `mlir.dialects.pto`

#### Serving Agent 是否需要其接口？

**❌ 不直接需要**

**理由**:
- Serving Agent 的 PyPTO 后端通过 **pypto** 模块生成 PTO 代码
- `pypto` 模块内部已经封装了与 PTOAS 的集成
- Serving Agent 只需调用 `pypto` 的 Python API，无需直接调用 PTOAS

**未来场景**:
- 如果 Serving Agent 需要支持 **自定义 PTO 优化 Pass**
- 如果 Serving Agent 需要直接操作 **PTO IR**（而非通过 pypto）

---

### 2. pto-isa (PTO Tile Library)

**仓库**: [PTO-ISA/pto-isa](https://github.com/PTO-ISA/pto-isa)

#### 功能定位

**PTO 虚拟指令集架构的 C++ 实现**，提供 90+ 标准 tile 级操作。

- **核心抽象**: Tile（硬件感知的数据块）
- **支持平台**: Ascend A2/A3/A5，CPU 模拟
- **操作类型**:
  - 矩阵运算: `TMATMUL`, `TMATMUL Collective`
  - 向量运算: `TADD`, `TMUL`, `TSIN`, `TEXP`
  - 数据搬运: `TLOAD`, `TSTORE`, `TEXTRACT`
  - 流水线控制: Event, Set Wait Flag, SFU

#### 技术特性

- **性能优化**: 封装底层硬件实现到 Tile 模板
- **跨平台兼容**: 同一份代码在不同 Ascend 架构上运行
- **编译模式**: Auto Mode（自动 buffer 管理）vs Manual Mode（手动 buffer 管理）

#### Serving Agent 是否需要其接口？

**❌ 不直接需要**

**理由**:
- pto-isa 是 **底层 C++ 库**，被编译后的内核调用
- Serving Agent 生成的 Rust/C++ 代码会 **链接 pto-isa 静态库**
- 无需在 Rust 层直接调用 PTO ISA API

**集成方式**:
```
Serving Agent 生成的代码
  ↓ (链接)
pto-isa 静态库 (.a)
  ↓ (调用)
PTO 内联函数/宏
```

**接口要求**:
- pto-isa 提供的 C++ API 应该 **稳定且文档化**
- 头文件路径清晰（`include/pto/`）
- 编译依赖明确（CMake `find_package` 或 `add_subdirectory`）

---

### 3. pypto (PyPTO 主框架)

**仓库**: [hw-native-sys/pypto](https://github.com/hw-native-sys/pypto)

#### 功能定位

**高性能 AI 加速器编程框架**，Tile 级编程模型。

- **多级 IR 系统**: Tensor Graph → Tile Graph → Block Graph → Execution Graph
- **编译 Pass**: 自动优化（循环展开、SSA、内存分配）
- **代码生成**: PTO 虚拟指令 → 目标平台可执行代码
- **执行调度**: MPMD (Multiple Program Multiple Data)

#### 核心抽象层次

| 层次 | 用户角色 | 编程模型 |
|------|---------|---------|
| **Tensor 级** | 算法开发者 | Tensor 操作（类似 NumPy） |
| **Tile 级** | 性能专家 | Tile 操作（显式数据分块） |
| **Block 级** | 系统开发者 | Block 操作（显式流水线） |

#### Python API 示例

```python
from pypto import ir

# Tensor 级编程（算法开发者）
@ir.function
def matmul(A: ir.Tensor[(M, K), ir.FP32],
           B: ir.Tensor[(K, N), ir.FP32]) -> ir.Tensor[(M, N), ir.FP32]:
    return ir.matmul(A, B)

# 编译到 PTO
module = ir.Module([matmul])
context = ir.CompileContext()
pto_code = context.compile_to_pto(module)
```

#### Serving Agent 是否需要其接口？

**✅ 必须**

**依赖关系**:
- Serving Agent 的 **PyPTO 后端代码生成器**需要调用 `pypto` API
- 具体来说，`serving_agent/pypto_codegen/` 模块需要：
  1. 构建 PyPTO IR（Tensor/Tile/Block 级）
  2. 运行编译 Pass
  3. 生成 PTO 代码
  4. 编译为 Ascend CCE 内核

#### **接口设计要求（AI 友好 + 开发友好）**

##### 要求 1: 清晰的分层 API

**问题**: pypto 当前 API 混合了多级抽象，AI 难以理解应该用哪一层。

**期望**:

```python
# ✅ 推荐：明确的分层 API
from pypto import tensor_level   # 算法开发者
from pypto import tile_level     # 性能专家
from pypto import block_level    # 系统开发者

# Serving Agent 默认使用 tensor_level
@tensor_level.function
def qwen3_attention(q, k, v, mask):
    return tensor_level.matmul(q, k.T) * mask  # 高级抽象
```

**当前状态**: 所有 API 都在 `pypto.ir` 命名空间下，缺乏分层导航。

##### 要求 2: 稳定的 IR 构造 API

**问题**: IR 节点构造方式频繁变化（`.create()` vs 工厂函数 vs 直接构造）。

**期望**:

```python
# ✅ 推荐：统一的工厂函数
tensor = ir.TensorExpr(shape, dtype)        # 一致性
scalar = ir.ScalarExpr(value)
call = ir.CallExpr(func, args)

# ❌ 避免：多种构造方式混用
tensor = ir.TensorExpr.create(shape, dtype)  # 有时用 create
tensor = ir.TensorExpr(shape, dtype)         # 有时直接构造
```

##### 要求 3: 编译流程简化

**问题**: 编译到 PTO 需要多个步骤（PassManager、Context、Strategy），AI 难以掌握。

**期望**:

```python
# ✅ 推荐：一键编译
pto_code = pypto.compile_to_pto(
    ir_function,
    target="ascend910b",
    optimization_level=2
)

# ❌ 避免：多步配置
context = ir.CompileContext()
pm = ir.PassManager()
pm.add_pass(ir.UnrollLoopsPass())
pm.add_pass(ir.ConvertToSSAPass())
# ... 10+ 行配置
pto_code = pm.run(module)
```

##### 要求 4: 错误信息可操作

**问题**: 编译错误信息技术性太强，难以定位问题。

**期望**:

```python
# ✅ 推荐：清晰的错误上下文
raise ValueError(
    "Invalid tile shape [16, 32] for matmul on Ascend910B:\n"
    "  - Inner dimension (32) must be multiple of 16 for TMATMUL\n"
    "  - Consider: reshape tensor to [16, 48] or [16, 64]"
)

# ❌ 避免：技术性错误
raise InternalError("Tile shape validation failed at line 1234")
```

##### 要求 5: 类型提示完整性

**问题**: Python API 缺少类型提示，IDE 无法自动补全。

**期望**:

```python
# ✅ 推荐：完整的类型提示
def matmul(A: TensorExpr, B: TensorExpr) -> TensorExpr:
    """Matrix multiplication.

    Args:
        A: Left operand, shape [M, K]
        B: Right operand, shape [K, N]

    Returns:
        Result tensor, shape [M, N]

    Raises:
        ValueError: If inner dimensions don't match
    """
    ...

# 自动补全应该能看到：
# - 参数类型
# - 返回类型
# - 文档字符串
# - 可能抛出的异常
```

##### 要求 6: 示例代码与测试覆盖

**问题**: 缺少端到端示例，AI 难以理解如何组合 API。

**期望**:

```python
# examples/compile_qwen3_layer.py
"""Complete example: Compile Qwen3 attention layer to PTO."""

from pypto import ir

def compile_qwen3_attention():
    # Step 1: Build IR
    @ir.function
    def attention(q, k, v, mask):
        score = ir.matmul(q, ir.transpose(k))
        score = score + mask
        weights = ir.softmax(score, axis=-1)
        return ir.matmul(weights, v)

    # Step 2: Compile to PTO
    pto_code = pypto.compile_to_pto(
        attention,
        target="ascend910b",
        optimization_level=2
    )

    # Step 3: Save to file
    with open("qwen3_attention.pto", "w") as f:
        f.write(pto_code)

    return pto_code

if __name__ == "__main__":
    compile_qwen3_attention()
```

---

### 4. pypto-lib (PyPTO 库)

**仓库**: [hw-native-sys/pypto-lib](https://github.com/hw-native-sys/pypto-lib)

#### 功能定位

**基于 PyPTO 的 Tensor 操作库 + 模型实现**。

- **tensor_functions/**: 常用 Tensor 操作（matmul, softmax, layernorm, etc.）
- **models/**: 完整模型实现（Qwen3, DeepSeek V3.2, GLM V4.5, etc.）
- **编码风格**: 遵循 `pypto-frontend-coding-style.md`

#### 设计目标

- 将 **PyPTO v2 的模型实现**迁移到新编码风格
- 所有函数定义为 **opaque functions**（不显式指定 orchestration/incore 边界）
- 依赖 `pypto` 模块的最新 API

#### Serving Agent 是否需要其接口？

**⚠️ 可选（推荐）**

**理由**:
- **短期**: Serving Agent 可以直接使用 `pypto` API 构建 IR
- **长期**: 使用 `pypto-lib` 的预定义 **tensor 函数**和**模型组件**，减少代码生成工作量

**集成策略**:

```python
# Serving Agent 生成代码时
from pypto_lib import tensor_functions as tf
from pypto_lib import models

# 使用预定义的 tensor 函数
@ir.function
def qwen3_mlp(hidden_states):
    # 重用 pypto-lib 的实现
    return tf.qwen3_mlp(
        hidden_states,
        gate_weight, up_weight, down_weight
    )

# 或者直接使用整个模型
model = models.Qwen3ForCausalLM(
    hidden_size=4096,
    num_layers=32
)
pto_code = pypto.compile_to_pto(model)
```

#### **接口设计要求**

##### 要求 1: 模块化组件

**问题**: 如果模型实现是单体函数，难以重用部分组件。

**期望**:

```python
# ✅ 推荐：模块化设计
from pypto_lib.models import qwen3
from pypto_lib.tensor_functions import attention, mlp, rms_norm

# 可以单独使用某个组件
layer = qwen3.TransformerLayer(
    attention=qwen3_attention,
    mlp=qwen3_mlp,
    norm_fn=rms_norm
)

# ❌ 避免：单体实现
# 无法单独重用 attention 或 mlp
model = qwen3.Qwen3ForCausalLM(...)
```

##### 要求 2: 配置驱动

**问题**: 模型参数硬编码，难以适配不同变体。

**期望**:

```python
# ✅ 推荐：配置驱动
from pypto_lib.models import qwen3

config = {
    "hidden_size": 4096,
    "num_layers": 32,
    "num_attention_heads": 32,
    "num_key_value_heads": 8,
    "intermediate_size": 11008,
    "max_position_embeddings": 32768,
}

model = qwen3.Qwen3ForCausalLM.from_config(config)

# ❌ 避免：硬编码
# 无法适配 Qwen3-0.5B, Qwen3-4B, Qwen3-32B 等变体
```

##### 要求 3: 版本兼容性

**问题**: `pypto-lib` 与 `pypto` 版本绑定，升级困难。

**期望**:

```python
# ✅ 推荐：版本兼容性检查
import pypto
import pypto_lib

if not pypto_lib.is_compatible_with(pypto.__version__):
    raise ImportError(
        f"pypto-lib {pypto_lib.__version__} requires "
        f"pypto {pypto_lib.min_pypto_version}, "
        f"got {pypto.__version__}"
    )
```

---

### 5. pypto-serving (PyPTO 推理引擎)

**仓库**: [hengliao1972/pypto-serving](https://github.com/hengliao1972/pypto-serving)

#### 功能定位

**超高性能推理引擎**，对标 vllm/sglang 子集。

- **语言**: C/C++（性能关键路径）
- **接口**: OpenAI 兼容（通过快速 IPC，非网络栈）
- **KV Cache**: Radix Tree 管理（持久化到 SSD）
- **运行时**: 依赖 `simpler` 的 PTO runtime
- **设计约束**: Python 代码禁止出现在 prefill/decode/KV cache 路径

#### 核心特性

1. **OpenAI 兼容接口**: `/v1/completions`, `/v1/chat/completions`
2. **Radix Tree KV Cache**: 类似 Sglang 的前缀匹配
3. **C++ 高性能路径**: 无 Python 开销
4. **测试路径**: 直接 IPC 注入测试数据（绕过网络栈）

#### Serving Agent 是否需要其接口？

**⚠️ 依赖关系（而非直接调用）**

**理由**:
- `pypto-serving` 本身就是一个 **推理引擎**
- Serving Agent 生成的代码 **可以作为 pypto-serving 的后端**
- 或者 Serving Agent 可以 **参考 pypto-serving 的架构**来生成推理服务

**两种集成模式**:

##### 模式 A: Serving Agent 生成独立服务

```
Serving Agent
  ↓ (生成)
独立 Rust 推理服务
  ↓ (链接)
simpler runtime + pto-isa
```

##### 模式 B: Serving Agent 生成 pypto-serving 插件

```
Serving Agent
  ↓ (生成)
PyPTO 内核 (.pto/.so)
  ↓ (加载)
pypto-serving (已有框架)
```

**推荐**: **模式 A**（Serving Agent 生成独立服务）

理由：
- Serving Agent 的目标是 **轻量级、可定制** 的服务
- `pypto-serving` 功能过于 **重型**（Radix Tree、持久化 KV Cache）
- 独立服务更容易 **适配不同场景**（单机/多机、不同并行策略）

#### **接口设计要求**

##### 要求 1: C ABI 清晰定义

**问题**: 如果 Serving Agent 生成的代码需要与 pypto-serving 互操作，需要稳定的 C ABI。

**期望**:

```c
// ✅ 推荐：稳定的 C ABI
typedef struct {
    void* dptr;
    size_t size;
} pto_tensor_t;

typedef struct {
    pto_tensor_t input;
    pto_tensor_t output;
    pto_tensor_t cache;
    int layer_id;
} pto_layer_args_t;

// 内核函数签名
extern "C" int pto_execute_layer(
    const pto_layer_args_t* args,
    void* stream
);
```

##### 要求 2: 内核注册机制

**问题**: pypto-serving 如何加载 Serving Agent 生成的内核？

**期望**:

```c
// ✅ 推荐：动态加载
typedef int (*pto_layer_fn)(const pto_layer_args_t*, void*);

// 内核插件入口点
extern "C" pto_layer_fn pto_get_layer_fn(int layer_id);
extern "C" const char* pto_get_layer_name(int layer_id);
extern "C" int pto_get_layer_version(void);

// pypto-serving 加载插件
void* handle = dlopen("qwen3_layer_0.so", RTLD_LAZY);
pto_layer_fn fn = (pto_layer_fn) dlsym(handle, "pto_get_layer_fn");
layer_executor = fn(0);  // 获取 layer 0 的执行函数
```

---

### 6. simpler (PTO Runtime)

**仓库**: [hw-native-sys/simpler](https://github.com/hw-native-sys/simpler)

#### 功能定位

**PTO 任务运行时执行框架**，协调 AICPU/AICore 执行。

- **三程序模型**: Host (.so) + AICPU (.so) + AICore (.o)
- **通信机制**: Handshake buffers（AICPU → AICore 任务分发）
- **平台支持**: a2a3（真实硬件）+ a2a3sim（线程模拟）
- **运行时变体**:
  - `host_build_graph`: Host 构建任务图
  - `aicpu_build_graph`: AICPU 构建任务图
  - `tensormap_and_ringbuffer`: 高级运行时（tensor map、ring buffer）

#### 架构细节

```
Python Application
  ↓ (ctypes)
Host Runtime (.so)  ← DeviceRunner, MemoryAllocator, C API
  ↓ (rtLaunchKernel)
AICPU Scheduler (.so)  ← 任务调度器
  ↓ (handshake buffers)
AICore Workers (.o)  ← 计算内核
```

#### Serving Agent 是否需要其接口？

**✅ 必须（如果使用 PTO 后端）**

**理由**:
- Serving Agent 生成的 **Ascend 内核**需要通过 simpler runtime 执行
- 至少需要 **Host Runtime 的 C API**（`pto_runtime_c_api.h`）
- 可能需要 **Python bindings**（`python/bindings.py`）

#### **接口设计要求（AI 友好 + 开发友好）**

##### 要求 1: C API 简洁明了

**问题**: 当前 C API 混合了 C++ 对象指针，难以理解。

**期望**:

```c
// ✅ 推荐：Opaque Pointer + 清晰的生命周期
// 初始化
pto_runtime_t* pto_runtime_init(
    int device_id,
    const char* aicpu_binary,
    const char* aicore_binary,
    const char* pto_isa_root
);

// 执行
int pto_runtime_run(
    pto_runtime_t* runtime,
    pto_task_graph_t* graph
);

// 清理
void pto_runtime_free(pto_runtime_t* runtime);

// ❌ 避免：混合 C++ 概念
DeviceRunner* runner = DeviceRunner::Get();  // C++ 单例
runner->Init(...);  // C++ 成员函数
```

##### 要求 2: 错误码标准化

**问题**: 错误处理不统一（-1, NULL, errno 混用）。

**期望**:

```c
// ✅ 推荐：标准错误码
typedef enum {
    PTO_SUCCESS = 0,
    PTO_ERROR_INVALID_ARG = -1,
    PTO_ERROR_OUT_OF_MEMORY = -2,
    PTO_ERROR_DEVICE_NOT_FOUND = -3,
    PTO_ERROR_KERNEL_LOAD_FAILED = -4,
    PTO_ERROR_EXECUTION_FAILED = -5,
} pto_error_code_t;

// 所有函数返回 pto_error_code_t
pto_error_code_t pto_runtime_run(
    pto_runtime_t* runtime,
    pto_task_graph_t* graph
);

// 错误信息查询
const char* pto_error_string(pto_error_code_t code);
```

##### 要求 3: 任务图构建 API

**问题**: 当前需要 C++ 代码构建任务图，Python 难以使用。

**期望**:

```c
// ✅ 推荐：C API 构建任务图
pto_task_graph_t* pto_graph_create(void);

// 添加任务
int pto_graph_add_task(
    pto_task_graph_t* graph,
    int task_id,
    pto_kernel_fn kernel,
    pto_tensor_t** inputs,
    int num_inputs,
    pto_tensor_t** outputs,
    int num_outputs
);

// 添加依赖
int pto_graph_add_dependency(
    pto_task_graph_t* graph,
    int task_id,
    int dependency_id
);

// 执行并等待
pto_error_code_t pto_graph_execute(
    pto_task_graph_t* graph,
    pto_runtime_t* runtime
);

void pto_graph_free(pto_task_graph_t* graph);

// ❌ 避免：需要 C++ 代码
Runtime* runtime = new Runtime();
runtime->AddTask(...);
runtime->AddDependency(...);
```

##### 要求 4: Python Bindings 易用性

**问题**: 当前 Python bindings 需要手动管理二进制加载。

**期望**:

```python
# ✅ 推荐：高级 Python API
from simpler import Runtime

# 自动查找并加载二进制
runtime = Runtime(
    platform="a2a3",  # 或 "a2a3sim"
    device_id=0,
    num_cores=4
)

# 构建任务图（Pythonic API）
graph = runtime.create_graph()
task_a = graph.add_task(kernel_a, inputs=[x], outputs=[y])
task_b = graph.add_task(kernel_b, inputs=[y], outputs=[z])
graph.add_dependency(task_b, on=task_a)

# 执行
graph.execute()

# ❌ 避免：手动加载
aicpu_bin = compile_aicpu(...)
aicore_bin = compile_aicore(...)
host_bin = compile_host(...)
Runtime = bind_host_binary(host_bin)
runtime = Runtime()
runtime.initialize()
launch_runtime(runtime, aicpu_binary=aicpu_bin, ...)
```

##### 要求 5: 内存管理自动化

**问题**: 需要手动分配/释放 device memory，容易出错。

**期望**:

```python
# ✅ 推荐：RAII 风格
with runtime.alloc_tensor(shape, dtype) as tensor:
    # tensor 自动分配 device memory
    runtime.copy_to_device(tensor, host_array)
    graph.execute(inputs=[tensor])
    result = graph.outputs[0]
    # tensor 自动释放

# 或者使用上下文管理器
with runtime.alloc_tensors([x, y, z]) as tensors:
    graph.execute(inputs=tensors)
# 所有 tensor 自动释放

# ❌ 避免：手动管理
ptr = runner.AllocateTensor(bytes)
try:
    runner.CopyToDevice(ptr, host_ptr, bytes)
    graph.execute()
finally:
    runner.FreeTensor(ptr)
```

##### 要求 6: 类型安全

**问题**: 使用 `void*` 传递 tensor，类型不安全。

**期望**:

```python
# ✅ 推荐：类型安全的 Tensor 对象
from simpler import Tensor

# 创建时指定 shape 和 dtype
tensor = Tensor(shape=[1024, 1024], dtype=DataType.FP32)
data = tensor.to_numpy()  # 获得 numpy view

# 运行时自动检查类型兼容性
graph.add_task(kernel, inputs=[tensor])  # 类型匹配检查

# ❌ 避免：void*
void* tensor = runner.AllocateTensor(...);  # 类型信息丢失
```

##### 要求 7: 文档与示例

**问题**: 当前 README 侧重架构，缺少 **入门示例**。

**期望**:

```python
# examples/hello_world.py
"""Minimal example: Add two vectors on Ascend NPU."""

from simpler import Runtime, Tensor
import numpy as np

def main():
    # 初始化运行时
    runtime = Runtime(platform="a2a3sim", device_id=0)

    # 分配输入 tensor
    a = Tensor.from_numpy(np.ones(1024, dtype=np.float32))
    b = Tensor.from_numpy(np.ones(1024, dtype=np.float32))
    c = Tensor.like(a)

    # 构建任务图
    graph = runtime.create_graph()
    add_task = graph.add_task(
        kernel="vector_add",  # 预注册的内核名称
        inputs=[a, b],
        outputs=[c]
    )

    # 执行
    graph.execute()

    # 获取结果
    result = c.to_numpy()
    print(f"Result: {result[:10]}")  # [2. 2. 2. ...]

if __name__ == "__main__":
    main()
```

---

### 7. pypto_runtime_distributed (Linqu Distributed Runtime)

**仓库**: [hengliao1972/pypto_runtime_distributed](https://github.com/hengliao1972/pypto_runtime_distributed)

#### 功能定位

**分布式运行时系统**，处理 L3-L6 层级分布式任务编排。

- **层级**: L6 (CLOS2) → L5 (CLOS1) → L4 (POD) → L3 (HOST)
- **通信**: Unix Socket / TCP / RDMA（跨节点）
- **架构**: 单进程编排模型（每个层级独立 OS 进程）
- **与 simpler 的关系**: **完全独立**，未来通过 `ChipBackend` 适配器桥接

#### 核心组件

- **LinquDaemon**: 每个节点的守护进程
- **LinquOrchestrator**: 集群协调器
- **LinquRuntimeOps**: 统一运行时 API（submit_task, scope_begin/end, alloc_tensor）
- **CodeCache/DataCache**: 内核/数据缓存
- **Ring Buffers**: 环形缓冲内存管理

#### Serving Agent 是否需要其接口？

**✅ 必须（如果需要多机分布式）**

**理由**:
- Serving Agent 的 **Phase 4: 多机分布式支持**需要 Linqu
- Linqu 提供 **L3-L6 的任务分发和协调**
- Serving Agent 生成的代码需要 **链接 Linqu Runtime**

**集成时间点**:
- **Phase 1-2**: 不需要（单机单卡/多卡）
- **Phase 3**: 不需要（配置生成）
- **Phase 4**: 需要（多机 Pipeline/Tensor Parallel）

#### **接口设计要求（AI 友好 + 开发友好）**

##### 要求 1: 统一的跨层级 API

**问题**: 当前每个层级有独立 API，难以统一管理。

**期望**:

```c
// ✅ 推荐：统一 API，自动路由到正确层级
// L3 HOST 层
linqu_runtime_t* linqu_runtime_init(
    linqu_level_t level,  // L3_HOST, L4_POD, L5_CLOS1, L6_CLOS2
    const char* config
);

// 提交任务（自动路由到目标层级）
int linqu_submit_task(
    linqu_runtime_t* runtime,
    const char* task_name,
    linqu_tensor_t** inputs,
    int num_inputs,
    linqu_tensor_t** outputs,
    int num_outputs
);

// ❌ 避免：每个层级独立 API
l3_runtime_submit_task(...)
l4_runtime_submit_task(...)
l5_runtime_submit_task(...)
```

##### 要求 2: 配置简化

**问题**: Linqu 启动需要复杂的拓扑配置。

**期望**:

```python
# ✅ 推荐：高层配置 API
from linqu import DistributedRuntime

# 自动发现拓扑
runtime = DistributedRuntime(
    level=linqu.L4_POD,
    discovery="auto",  # 自动查找同级节点
    transport="tcp"    # 或 "rdma"
)

# 或者手动指定节点
runtime = DistributedRuntime(
    level=linqu.L4_POD,
    peers=[
        "192.168.1.1:29500",
        "192.168.1.2:29500",
        "192.168.1.3:29500",
        "192.168.1.4:29500",
    ]
)

# ❌ 避免：手动配置每个层级
l3_config = {...}
l4_config = {...}
l5_config = {...}
l6_config = {...}
```

##### 要求 3: 故障处理透明

**问题**: 节点故障需要手动处理。

**期望**:

```python
# ✅ 推荐：自动故障恢复
runtime = DistributedRuntime(
    level=linqu.L4_POD,
    fault_tolerance="auto",  # 自动重启失败节点
    max_retries=3
)

# 提交任务时自动处理故障
future = runtime.submit_task(task, timeout=30.0)
try:
    result = future.result()  # 自动重试
except LinquNodeFailure as e:
    print(f"Node {e.node_id} failed, retried on {e.retry_node}")

# ❌ 避免：手动检测和重试
try:
    result = runtime.submit_task(task)
except NodeFailure:
    # 手动查找新节点
    new_node = find_available_node()
    result = runtime.submit_task_on_node(task, new_node)
```

##### 要求 4: 与 simpler 的集成点清晰

**问题**: L3 → L2 dispatch 当前是 stub，未来如何集成不明确。

**期望**:

```c
// ✅ 推荐：明确的适配器接口
// Linqu 侧
typedef int (*linqu_chip_backend_fn)(
    const char* kernel_name,
    void* inputs,
    void* outputs,
    void* stream
);

// 注册 ChipBackend（指向 simpler runtime）
void linqu_register_chip_backend(
    linqu_runtime_t* runtime,
    linqu_chip_backend_fn backend_fn,
    void* backend_context
);

// Simpler 侧
// 提供 C ABI wrapper
extern "C" int simpler_dispatch_task(
    void* simpler_runtime,
    const char* kernel_name,
    void* inputs,
    int num_inputs,
    void* outputs,
    int num_outputs
);

// 集成代码
linqu_register_chip_backend(
    linqu_runtime,
    simpler_dispatch_task,
    simpler_runtime_ptr
);

// ❌ 避免：硬编码依赖
// Linqu 直接链接 simpler 的 C++ 代码
```

##### 要求 5: 性能可观测性

**问题**: 缺少性能 profiling 接口。

**期望**:

```python
# ✅ 推荐：内置 profiling
runtime = DistributedRuntime(
    level=linqu.L4_POD,
    enable_profiling=True
)

with runtime.profile() as prof:
    result = runtime.submit_task(task)

# 打印性能报告
print(prof.report())
# Task execution:
#   - Compute: 10.2ms
#   - Communication: 2.3ms
#   - Synchronization: 0.5ms
# Ring buffer usage:
#   - Peak: 80% (1024/1280 slots)
#   - Average: 45%

# 导出为 JSON
prof.export_json("profile.json")

# ❌ 避免：无 profiling 信息
result = runtime.submit_task(task)
# 不知道性能瓶颈在哪
```

##### 要求 6: Python 易用性

**问题**: 当前 API 主要是 C，Python 需要手动 ctypes。

**期望**:

```python
# ✅ 推荐：原生 Python API
from linqu import DistributedRuntime, Tensor

# 初始化（Pythonic）
runtime = DistributedRuntime(
    level=linqu.L4_POD,
    peers=["node1:29500", "node2:29500"]
)

# 提交任务（支持 NumPy）
import numpy as np
data = Tensor.from_numpy(np.random.rand(1024, 1024))
result = runtime.submit_task("matmul", inputs=[data, weight])

# 异步执行
future = runtime.submit_task_async("matmul", inputs=[data, weight])
result = future.wait(timeout=30.0)

# ❌ 避免：ctypes 手动绑定
lib = ctypes.CDLL("liblinqu.so")
lib.linqu_submit_task.argtypes = [...]
result = lib.linqu_submit_task(...)
```

---

## Serving Agent 集成策略

### 阶段化集成路线图

#### Phase 1: 单机单卡（Week 1-4）

**目标**: 生成基本的 PyPTO Ascend 后端

**依赖模块**:
- ✅ `pypto` - 核心 IR 构建
- ✅ `PTOAS` - 代码生成（通过 pypto 间接调用）
- ✅ `pto-isa` - 链接静态库
- ✅ `simpler` - Host Runtime C API

**不需要**:
- ❌ `pypto-lib` - 可选（未来可复用 tensor 函数）
- ❌ `pypto-serving` - 不适用（独立服务）
- ❌ `pypto_runtime_distributed` - 不需要（单机）

**集成方式**:

```rust
// rust_llm_server/src/ops/pypto.rs
use simpler_sys::{pto_runtime_init, pto_runtime_run};

pub struct PyPTOComputeOps {
    runtime: *mut simpler_sys::pto_runtime_t,
    device_id: i32,
}

impl PyPTOComputeOps {
    pub fn new(device_id: i32) -> Result<Self> {
        // 初始化 simpler runtime
        let runtime = unsafe {
            simpler_sys::pto_runtime_init(
                device_id,
                std::ptr::null(),  // aicpu_binary（后续加载）
                std::ptr::null(),  // aicore_binary
                std::ptr::null(),  // pto_isa_root（自动查找）
            )
        };

        Ok(Self { runtime, device_id })
    }
}
```

#### Phase 2: 单机多卡 TP（Week 5-8）

**目标**: 基于 PyPTO 通信的 Tensor Parallel

**依赖模块**:
- ✅ `pypto` - 通信原语（TPUSH/TPOP）
- ✅ `simpler` - 多卡 Host Runtime
- ⚠️ `pypto_runtime_distributed` - **可能需要 L3 HOST 层**

**集成方式**:

```rust
// 使用 PyPTO TPUSH/TPOP
use pypto::comm::{tpush, tpop};

pub struct PyPTOCommunicator {
    rank: usize,
    world_size: usize,
    stream: *mut ascend::Stream,
}

impl PyPTOCommunicator {
    pub fn all_reduce(&self, tensor: &mut DeviceTensor) {
        // 使用 PyPTO Ring AllReduce
        for step in 0..self.world_size {
            let next_rank = (self.rank + 1) % self.world_size;
            let prev_rank = (self.rank - 1 + self.world_size) % self.world_size;

            unsafe {
                // 发送到下一跳
                tpush(
                    tensor.as_ptr(),
                    tensor.size(),
                    direction_to_rank(next_rank),
                    tag,
                    self.stream,
                );

                // 从上一跳接收
                tpop(
                    tensor.as_ptr(),
                    tensor.size(),
                    direction_from_rank(prev_rank),
                    tag,
                    self.stream,
                );

                // 本地累加
                ascend::device_add_inplace(tensor, received);
            }
        }
    }
}
```

#### Phase 3: 配置生成（Week 9-12）

**目标**: Serving Agent 模板引擎

**依赖模块**:
- ✅ `pypto` - 生成 PTO 代码
- ⚠️ `pypto-lib` - **可选**（复用 tensor 函数）

**集成方式**:

```python
# serving_agent/pypto_codegen/qwen3_kernelgen.py
from pypto import ir, compile

class Qwen3KernelGenerator:
    def __init__(self, spec: LayerSpec):
        self.spec = spec

    def generate_attention_kernel(self) -> ir.Module:
        """生成 Flash Attention 内核（PyPTO IR）"""

        @ir.function
        def flash_attention(
            q: ir.Tensor[(B, H, S, D), ir.FP16],
            k: ir.Tensor[(B, H, S, D), ir.FP16],
            v: ir.Tensor[(B, H, S, D), ir.FP16],
            mask: ir.Tensor[(B, 1, S, S)], ir.FP16,
        ) -> ir.Tensor[(B, H, S, D), ir.FP16]:
            # 使用 pypto-lib 的预定义函数（如果可用）
            from pypto_lib.tensor_functions import attention
            return attention.flash_attention(q, k, v, mask)

        return ir.Module([flash_attention])

    def compile_all(self, output_dir: str) -> List[str]:
        """编译为 Ascend CCE 二进制"""
        for name, program in self.kernels:
            # 调用 pypto 编译到 PTO
            pto_code = compile.compile_to_pto(program, target="ascend910b")

            # 保存 .pto 文件
            pto_path = f"{output_dir}/{name}.pto"
            with open(pto_path, "w") as f:
                f.write(pto_code)

            # 调用 PTOAS 编译到 CCE
            ptoas.compile(pto_path, output=f"{output_dir}/{name}.so")
```

#### Phase 4: 多机分布式（Week 13-16）

**目标**: 跨机器 Pipeline/Tensor Parallel

**依赖模块**:
- ✅ `pypto_runtime_distributed` - **必须**（L3-L6 协调）
- ✅ `simpler` - L0-L2 执行（通过 ChipBackend 适配器）
- ✅ `pypto` - 通信原语

**集成方式**:

```rust
// rust_llm_server/src/distributed/linqu_adapter.rs
use linqu_sys::{linqu_runtime_init, linqu_submit_task};

pub struct LinquDistributedBackend {
    l3_runtime: *mut linqu_sys::linqu_runtime_t,
    simpler_backend: simpler_sys::pto_runtime_t,
}

impl LinquDistributedBackend {
    pub fn init(
        rank: usize,
        world_size: usize,
        level: LinquLevel,
    ) -> Result<Self> {
        // 初始化 Linqu L3 runtime
        let l3_runtime = unsafe {
            linqu_sys::linqu_runtime_init(
                linqu_sys::L3_HOST,
                rank,
                world_size,
            )
        };

        // 初始化 simpler runtime（L0-L2）
        let simpler_backend = unsafe {
            simpler_sys::pto_runtime_init(
                device_id,
                aicpu_binary,
                aicore_binary,
                pto_isa_root,
            )
        };

        // 注册 ChipBackend 适配器
        unsafe {
            linqu_sys::linqu_register_chip_backend(
                l3_runtime,
                Some(l3_to_l2_dispatch),
                simpler_backend as *mut _,
            );
        }

        Ok(Self { l3_runtime, simpler_backend })
    }
}

// L3 → L2 dispatch 函数
extern "C" fn l3_to_l2_dispatch(
    simpler_runtime: *mut simpler_sys::pto_runtime_t,
    kernel_name: *const c_char,
    inputs: *mut *mut c_void,
    num_inputs: usize,
    outputs: *mut *mut c_void,
    num_outputs: usize,
) -> i32 {
    unsafe {
        // 调用 simpler runtime 执行任务
        simpler_sys::pto_runtime_run(
            simpler_runtime,
            /* 构建 task graph */
        )
    }
}
```

---

## 接口设计要求总结

### 按 AI 友好性分类

#### 高优先级（影响 AI 理解和使用）

| 要求 | 影响模块 | 具体描述 |
|------|---------|---------|
| **清晰的分层 API** | `pypto` | Tensor/Tile/Block 三层 API 分离，AI 容易选择正确层次 |
| **一键编译** | `pypto` | `compile_to_pto(ir)` 替代多步 PassManager 配置 |
| **可操作的错误信息** | 所有模块 | 错误消息包含上下文和解决方案 |
| **示例代码覆盖** | 所有模块 | 每个核心功能有可运行的示例 |
| **配置驱动** | `pypto-lib` | 模型通过配置文件适配不同变体 |
| **高层 Python API** | `simpler`, `linqu` | 隐藏 ctypes/二进制加载细节 |
| **自动化内存管理** | `simpler` | RAII 风格，自动释放 device memory |

#### 中优先级（影响开发效率）

| 要求 | 影响模块 | 具体描述 |
|------|---------|---------|
| **类型提示完整性** | `pypto`, `pypto-lib` | Python API 完整的类型提示 |
| **稳定的 IR 构造 API** | `pypto` | 统一的工厂函数，避免多种构造方式 |
| **标准错误码** | `simpler`, `linqu` | C API 使用枚举错误码，而非 -1/NULL |
| **版本兼容性检查** | `pypto-lib` | 与 `pypto` 版本兼容性自动检查 |
| **故障恢复透明** | `linqu` | 自动重试和故障转移 |
| **性能可观测性** | `linqu` | 内置 profiling 和性能报告 |

#### 低优先级（长期改进）

| 要求 | 影响模块 | 具体描述 |
|------|---------|---------|
| **模块化组件** | `pypto-lib` | 可以单独重用模型组件（attention/mlp） |
| **C ABI 清晰定义** | `pypto-serving` | 插件式内核加载的稳定 ABI |
| **统一跨层级 API** | `linqu` | 一个 API 处理 L3-L6 所有层级 |

### 按开发友好性分类

#### API 设计原则

1. **最小惊讶原则** (Principle of Least Astonishment)
   - API 行为符合用户直觉
   - 命名一致（例如都是 `create_*()` 或都是 `*_new()`）

2. **渐进式披露** (Progressive Disclosure)
   - 简单用例简单 API，复杂用例暴露高级选项
   - 示例：`compile_to_pto(ir)` vs `compile_to_pto(ir, opt_level=2, passes=[...])`

3. **失败快速** (Fail Fast)
   - 参数校验在 API 边界完成
   - 错误信息包含参数名称和期望值

4. **默认值合理** (Sensible Defaults)
   - 例如 `compile_to_pto(ir, target="ascend910b")` 有合理默认值
   - 用户只在需要时覆盖

5. **文档即测试** (Documentation as Tests)
   - 示例代码应该可以运行
   - 测试框架验证示例正确性

---

## 优先级路线图

### 短期（1-2 个月）

**目标**: 支持 Phase 1-2（单机单卡/多卡）

**关键接口改进**:

1. **pypto**:
   - [ ] 分层 API（`pypto.tensor_level`, `pypto.tile_level`, `pypto.block_level`）
   - [ ] 一键编译函数 `compile_to_pto()`
   - [ ] 可操作的错误信息

2. **simpler**:
   - [ ] 标准 C 错误码（`pto_error_code_t`）
   - [ ] C API 任务图构建（`pto_graph_*`）
   - [ ] 高层 Python bindings（隐藏 ctypes）

3. **文档**:
   - [ ] pypto 快速入门（5 分钟上手）
   - [ ] simpler Hello World 示例
   - [ ] Serving Agent 集成示例

### 中期（3-4 个月）

**目标**: 支持 Phase 3（配置生成）

**关键接口改进**:

1. **pypto-lib**:
   - [ ] 配置驱动的模型 API（`from_config()`）
   - [ ] 模块化组件（单独重用 attention/mlp）
   - [ ] 版本兼容性检查

2. **PTOAS**:
   - [ ] 稳定的 CLI 参数（不频繁变化）
   - [ ] Python 绑定示例（如何调用 ptoas）

3. **文档**:
   - [ ] pypto-lib API 参考
   - [ ] 配置文件规范（TOML Schema）
   - [ ] 端到端案例：从配置到运行

### 长期（5-6 个月）

**目标**: 支持 Phase 4-5（多机分布式 + 性能优化）

**关键接口改进**:

1. **pypto_runtime_distributed**:
   - [ ] 高层 Python API（`DistributedRuntime`）
   - [ ] 自动拓扑发现
   - [ ] 内置 profiling

2. **pto-isa**:
   - [ ] 稳定的 C++ API 文档
   - [ ] 性能调优指南
   - [ ] Auto Mode vs Manual Mode 对比

3. **文档**:
   - [ ] Linqu 分布式编程指南
   - [ ] 多机配置示例
   - [ ] 性能优化最佳实践

---

## 附录：关键接口示例

### A. PyPTO IR 构建（期望接口）

```python
# examples/build_qwen3_layer.py
"""Build Qwen3 transformer layer using PyPTO IR."""

from pypto import tensor_level as tl
from pypto import compile

# 定义层配置
config = {
    "hidden_size": 4096,
    "num_attention_heads": 32,
    "num_key_value_heads": 8,
    "intermediate_size": 11008,
}

# 构建注意力层
@tl.function
def qwen3_attention(
    hidden_states: tl.Tensor[(B, S, H), tl.FP16],
    attention_mask: tl.Tensor[(B, 1, S, S), tl.FP16],
) -> tl.Tensor[(B, S, H), tl.FP16]:
    # QKV 投影
    qkv = tl.linear(hidden_states, (3 * H,), bias=None)
    q, k, v = tl.split(qkv, 3, axis=-1)

    # 多头注意力
    q = tl.reshape(q, (B, S, num_heads, head_dim))
    k = tl.reshape(k, (B, S, num_kv_heads, head_dim))
    v = tl.reshape(v, (B, S, num_kv_heads, head_dim))

    # Flash Attention
    attn_output = tl.flash_attention(q, k, v, attention_mask)

    # 输出投影
    output = tl.linear(attn_output, (H,), bias=None)
    return output

# 编译到 PTO
try:
    pto_code = compile.compile_to_pto(
        qwen3_attention,
        target="ascend910b",
        optimization_level=2,
    )
    print("✅ Compilation successful")
except ValueError as e:
    print(f"❌ Compilation failed: {e}")
    print("💡 Hint: Check that tensor shapes are compatible")
```

### B. Simpler Runtime 使用（期望接口）

```python
# examples/run_on_ascend.py
"""Run kernel on Ascend NPU using Simpler runtime."""

from simpler import Runtime, Tensor
import numpy as np

def main():
    # 初始化运行时（自动查找二进制）
    runtime = Runtime(
        platform="a2a3",  # 或 "a2a3sim" 用于模拟
        device_id=0,
        num_cores=4,
    )

    # 分配 tensor（自动管理内存）
    with runtime.alloc_tensors([
        Tensor([1024, 1024], DataType.FP16),  # input
        Tensor([1024, 1024], DataType.FP16),  # weight
        Tensor([1024, 1024], DataType.FP16),  # output
    ]) as (input, weight, output):
        # 复制数据到 device
        input.copy_from_numpy(np.random.rand(1024, 1024))
        weight.copy_from_numpy(np.random.rand(1024, 1024))

        # 构建任务图
        graph = runtime.create_graph()
        matmul_task = graph.add_task(
            kernel="matmul_fp16",  # 预注册的内核
            inputs=[input, weight],
            outputs=[output],
        )

        # 执行并自动同步
        graph.execute()

        # 获取结果
        result = output.to_numpy()
        print(f"Result shape: {result.shape}")
        print(f"First 10 elements: {result[0, :10]}")

if __name__ == "__main__":
    main()
```

### C. Linqu 分布式运行时（期望接口）

```python
# examples/distributed_inference.py
"""Distributed inference across 4 nodes."""

from linqu import DistributedRuntime, Tensor
import numpy as np

def main():
    # 初始化分布式运行时（自动发现拓扑）
    runtime = DistributedRuntime(
        level=linqu.L4_POD,
        discovery="auto",  # 自动查找同级节点
        transport="tcp",
        fault_tolerance="auto",  # 自动故障恢复
    )

    # 获取当前节点信息
    print(f"Rank: {runtime.rank}/{runtime.world_size}")

    # 分片数据（Tensor Parallel）
    local_hidden_size = 4096 // runtime.world_size
    input = Tensor([32, local_hidden_size], DataType.FP16)
    input.copy_from_numpy(np.random.rand(32, local_hidden_size))

    # 提交任务到远程节点（自动路由）
    output = runtime.submit_task(
        "qwen3_layer",
        inputs=[input, layer_id],
        timeout=30.0,
    )

    # 收集结果（AllReduce 自动处理）
    result = output.to_numpy()
    print(f"Output shape: {result.shape}")

if __name__ == "__main__":
    main()
```

---

## 结论

### 核心发现

1. **pypto 是关键依赖** - Serving Agent **必须**使用其 API 进行 IR 构建和代码生成
2. **simpler 是运行时基础** - 单机场景 **必须**使用其 C API/Python bindings
3. **pypto_runtime_distributed 是多机必需** - 多机场景 **必须**使用 Linqu 进行 L3-L6 协调
4. **pypto-lib 是可选加速器** - 可以复用其 tensor 函数和模型组件，减少代码生成工作量
5. **PTOAS 和 pto-isa 是间接依赖** - 通过 pypto 和 simpler 间接使用，无需直接调用

### 接口改进优先级

**最高优先级（阻塞 Serving Agent 开发）**:
1. pypto 一键编译 API
2. simpler 标准 C 错误码
3. simpler 高层 Python API
4. pypto 可操作的错误信息

**高优先级（显著提升开发效率）**:
5. pypto 分层 API
6. simpler C API 任务图构建
7. pypto-lib 配置驱动模型
8. 完整的示例代码

**中优先级（长期改进）**:
9. Linqu 高层 Python API
10. Linqu 自动拓扑发现
11. pto-isa 稳定的 C++ API 文档

### 下一步行动

1. **与 pypto 团队对齐** - 讨论一键编译 API 和分层 API 的设计
2. **与 simpler 团队对齐** - 讨论标准错误码和高层 Python API 的实现
3. **与 pypto-lib 团队对齐** - 讨论配置驱动模型的设计
4. **建立接口规范文档** - 基于本文档的要求，创建详细的 API 规范
5. **启动接口改进 PoC** - 选择 1-2 个最高优先级接口，实现改进原型

---

**文档维护者**: Claude (Sonnet 4.5)
**反馈渠道**: 请在项目 Issue 中提出接口改进建议
