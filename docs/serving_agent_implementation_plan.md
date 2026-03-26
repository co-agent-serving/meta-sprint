# Serving Agent 项目实施计划

## 项目概述

开发一个 **Serving Agent** 系统，能够根据部署需求（硬件、模型等）自动生成轻量级的 LLM 推理服务框架。

### 核心定位
- **PyPTO 作为唯一后端**：统一的 Tile 级抽象
- **硬件支持**：Ascend NPU
- **代码统一**：同一份 PyPTO 后端代码，无需多套实现

### 核心动机
1. **现有栈复杂**：vllm-ascend + pytorch-npu + CANN 版本匹配复杂、环境要求高、代码量大（>10万行），AI 难以全面理解和调试
2. **需求差异大**：不同场景需要不同特性（单机/多机、KV cache 策略、批处理方式等），通用框架臃肿
3. **开发调试困难**：需要统一的推理框架简化开发流程

### 近期目标
1. **PyPTO Ascend 后端**：生成 Ascend 内核，支持生产部署
2. **多机分布式**：基于 PyPTO 通信原语实现跨机器推理

---

## 架构设计

### 整体架构

Serving Agent 采用 **三阶段流水线**：

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

### 核心组件

| 组件 | 位置 | 功能 |
|------|------|------|
| **Config Parser** | `serving_agent/config/` | 解析和验证用户配置 |
| **Template Engine** | `serving_agent/templates/` | Jinja2 模板代码生成 |
| **Project Assembler** | `serving_agent/assembler/` | 组装完整 Rust 项目 |
| **PyPTO Codegen** | `serving_agent/pypto_codegen/` | PyPTO 内核生成 |

### 模板库架构

```
serving_agent/templates/
├── core/                    # 核心服务器组件
│   ├── main.rs.j2
│   ├── engine.rs.j2
│   └── scheduler.rs.j2
├── backends/                 # 计算后端变体
│   ├── aclnn/               # Ascend aclnn 后端
│   └── pypto/               # PyPTO 后端（新增）
│       ├── ops.rs.j2
│       ├── pto_runner.rs.j2
│       └── kernelgen.rs.j2
├── parallel/                 # 并行策略
│   ├── single_node.rs.j2
│   ├── tensor_parallel.rs.j2
│   └── pipeline_parallel.rs.j2
└── communication/            # 通信层
    ├── local.rs.j2          # 单机
    ├── hccl.rs.j2           # HCCL 多卡
    └── distributed.rs.j2    # TCP/RDMA 多机
```

---

## 实施路线图

### Phase 1: PyPTO 后端基础（第 1-4 周）

**目标**：实现 PyPTO Ascend 后端

#### 交付物

1. **统一 ComputeOps 接口（保持不变）**
   - 文件：`rust_llm_server/src/ops/stubs.rs`（保持）
   - 功能：定义算子 trait，所有后端实现

2. **PyPTO Ascend 后端实现（生产用）**
   - 文件：`rust_llm_server/src/ops/pypto.rs`（新建）
   - 功能：PyPTO 生成的 Ascend CCE 内核
   - 接口：
   ```rust
   pub struct PyPTOComputeOps {
       device: ascend::Device,
       stream: ascend::Stream,
       device_id: i32,
       runtime_lib: libloading::Library,  // PyPTO runtime
       kernel_cache: HashMap<String, CompiledKernel>,
   }

   impl PyPTOComputeOps {
       /// 初始化 PyPTO Ascend 后端
       pub fn new(device_id: Option<i32>) -> Result<Self> {
           let device = ascend::Device::init(device_id.unwrap_or(0))?;
           let stream = ascend::Stream::new()?;
           let runtime_lib = unsafe {
               libloading::Library::new("libpypto_runtime.so")?
           };
           Ok(Self { device, stream, device_id, runtime_lib, kernel_cache: HashMap::new() })
       }

       /// 执行 PyPTO 编译的内核
       unsafe fn execute_pypto_kernel(
           &self,
           kernel_handle: *mut c_void,
           inputs: &[&DeviceTensor],
           outputs: &mut [&mut DeviceTensor],
       ) -> Result<()> {
           let pypto_run = self.runtime_lib.get::<PyPTORunFn>(b"pypto_run")?;
           pypto_run(kernel_handle, inputs, outputs)?;
           Ok(())
       }
   }

   impl ComputeOps for PyPTOComputeOps {
       fn matmul(&self, a: &Tensor, b: &Tensor, out: &mut Tensor) {
           // 使用 PyPTO 生成的 matmul 内核
       }
       // ... 其他算子
   }
   ```

3. **PyPTO 内核生成器（仅 Ascend）**
   - 文件：`serving_agent/pypto_codegen/qwen3_kernelgen.py`
   - 功能：生成 Qwen3 的 Ascend CCE 内核
   ```python
   class Qwen3KernelGenerator:
       """生成 Ascend NPU 的 PyPTO 内核"""

       def __init__(self, spec: LayerSpec):
           self.spec = spec

       def generate_attention_kernel(self) -> ir.Program:
           """生成 Flash Attention 内核（Ascend 优化）"""

       def generate_mlp_kernel(self) -> ir.Program:
           """生成 MLP (SwiGLU) 内核"""

       def compile_all(self, output_dir: str) -> List[str]:
           """编译为 CCE 二进制（.so 文件）"""
           for name, program in self.kernels:
               pypto.runtime.compile_program(
                   program,
                   work_dir=f"{output_dir}/{name}",
                   backend=pypto.backend.BackendType.Ascend910B_CCE,
               )
   ```

4. **构建脚本（条件编译）**
   - 文件：`rust_llm_server/build.rs`
   ```rust
   fn main() {
       // 检测 BACKEND 环境变量
       let backend = std::env::var("BACKEND").unwrap_or("pypto".to_string());

       match backend.as_str() {
           "pypto" => {
               // 运行 PyPTO 内核生成
               let output = std::process::Command::new("python3")
                   .arg("../serving_agent/pypto_codegen/qwen3_kernelgen.py")
                   .arg("--output")
                   .arg("target/pypto_kernels")
                   .status()
                   .expect("PyPTO kernel gen failed");

               // 链接生成的内核
               println!("cargo:rustc-link-search=target/pypto_kernels");
               println!("cargo:rustc-cfg=backend=\"pypto\"");
           }
           _ => panic!("Unknown backend: {}", backend),
       }
   }
   ```

5. **OpsBundle 支持**
   - 文件：`rust_llm_server/src/ops/mod.rs`
   ```rust
   impl OpsBundle {
       /// PyPTO Ascend 后端（生产）
       pub fn pypto_ascend(device_id: Option<i32>) -> Result<Self> {
           Ok(Self {
               compute: Box::new(PyPTOComputeOps::new(device_id)?),
               comm: Box::new(PyPTOCommOps::new(device_id)?),  // PyPTO 通信
               quant: Box::new(PyPTOQuantOps::new(device_id)?),
           })
       }
   }
   ```

#### 验收标准

**Week 1-4: PyPTO Ascend 后端**：
- ✅ PyPTO 生成 Ascend 内核
- ✅ Qwen3-0.6B 在 Ascend 910B 上推理
- ✅ 输出与参考值一致（数值验证）
- ✅ 内核编译时间 < 30s

#### 关键文件
- `rust_llm_server/src/ops/pypto.rs`（新建，PyPTO Ascend 后端）
- `rust_llm_server/src/ops/mod.rs`（修改，PyPTO 后端支持）
- `rust_llm_server/build.rs`（修改，条件编译）
- `rust_llm_server/Cargo.toml`（修改，可选依赖）
- `serving_agent/pypto_codegen/qwen3_kernelgen.py`（新建，仅 Ascend）

---

### Phase 2: 分布式通信基础（第 5-8 周）

**目标**：基于 PyPTO 通信原语实现分布式推理

#### 架构决策

**统一使用 PyPTO 通信**：
- **单机多卡**：PyPTO intra-cluster 通信（TPUSH/TPOP）
- **多机多卡**：PyPTO inter-cluster 通信

#### 交付物

1. **PyPTO 通信 FFI 绑定**
   - 文件：`rustBindings/pypto-sys/src/comm.rs`（新建）
   ```rust
   extern "C" {
       fn pypto_push(
           tensor: *const c_void,
           size: usize,
           direction: u32,  // 0-7
           tag: u32,
           stream: *mut c_void,
       ) -> i32;

       fn pypto_pop(
           tensor: *mut c_void,
           size: usize,
           direction: u32,
           tag: u32,
           stream: *mut c_void,
       ) -> i32;

       fn pypto_comm_init(
           nranks: usize,
           rank: usize,
           comm_type: PyPTOCommType,
       ) -> *mut PyPTOComm;
   }
   ```

2. **PyPTO 通信安全封装**
   - 文件：`rustBindings/ascend/src/pypto_comm.rs`（新建）
   ```rust
   pub struct PyPTOCommunicator {
       comm: *mut pypto_sys::PyPTOComm,
       rank: usize,
       world_size: usize,
       stream: ascend::Stream,
   }

   impl PyPTOCommunicator {
       pub fn init(
           rank: usize,
           world_size: usize,
           comm_type: PyPTOCommType,
           stream: &ascend::Stream,
       ) -> Result<Self> {
           let comm = unsafe {
               pypto_sys::pypto_comm_init(world_size, rank, comm_type)
           };
           Ok(Self { comm, rank, world_size, stream: stream.clone() })
       }

       pub fn all_reduce_sum(&self, tensor: &mut DeviceTensor) -> Result<()> {
           // 使用 PyPTO TPUSH/TPOP 实现 Ring AllReduce
       }

       pub fn send(&self, tensor: &DeviceTensor, dst_rank: usize) -> Result<()>;
       pub fn recv(&self, tensor: &mut DeviceTensor, src_rank: usize) -> Result<()>;
   }
   ```

3. **PyPTOCommOps 实现**
   - 文件：`rust_llm_server/src/ops/pypto_comm.rs`（新建）
   ```rust
   pub struct PyPTOCommOps {
       comm: PyPTOCommunicator,
   }

   impl PyPTOCommOps {
       pub fn new(
           device_id: i32,
           rank: usize,
           world_size: usize,
       ) -> Result<Self> {
           let device = ascend::Device::init(device_id)?;
           let stream = ascend::Stream::new()?;
           let comm = PyPTOCommunicator::init(
               rank,
               world_size,
               PyPTOCommType::IntraCluster,
               &stream,
           )?;
           Ok(Self { comm })
       }
   }

   impl CommOps for PyPTOCommOps {
       fn all_reduce_sum(&self, tensor: &mut Tensor) {
           let device_tensor = tensor.to_device_tensor()?;
           self.comm.all_reduce_sum(&mut device_tensor)?;
       }

       fn all_gather(&self, input: &Tensor, out: &mut Tensor);
       fn send(&self, tensor: &Tensor, dst_rank: usize);
       fn recv(&self, out: &mut Tensor, src_rank: usize);
   }
   ```

4. **OpsBundle 扩展**
   - 文件：`rust_llm_server/src/ops/mod.rs`
   ```rust
   impl OpsBundle {
       /// PyPTO 后端 + PyPTO 通信
       pub fn pypto_distributed(
           device_id: i32,
           rank: usize,
           world_size: usize,
       ) -> Result<Self> {
           Ok(Self {
               compute: Box::new(PyPTOComputeOps::new(device_id)?),
               comm: Box::new(PyPTOCommOps::new(device_id, rank, world_size)?),
               quant: Box::new(PyPTOQuantOps::new(device_id)?),
           })
       }
   }
   ```

#### 验收标准

**Week 5-8: NPU 模式**：
- ✅ TP=2 在单机 2 卡 Ascend 上运行
- ✅ PyPTO TPUSH/TPOP 通信正确
- ✅ AllReduce 延迟 < 100μs
- ✅ Qwen3-8B TP=2 输出正确

#### 关键文件
- `rustBindings/pypto-sys/src/comm.rs`（新建）
- `rustBindings/ascend/src/pypto_comm.rs`（新建）
- `rust_llm_server/src/ops/pypto_comm.rs`（新建）
- `rust_llm_server/src/ops/mod.rs`（修改）

---

### Phase 3: Serving Agent 原型（第 9-12 周）

**目标**：基础代码生成功能，可从配置生成服务器

#### 交付物

1. **配置解析器**
   - 文件：`serving_agent/config/spec.rs`（新建）
   - 功能：TOML/JSON → ConfigSpec
   ```rust
   #[derive(Debug, Deserialize)]
   pub struct ServingConfig {
       pub model: ModelConfig,
       pub hardware: HardwareConfig,
       pub backend: BackendConfig,
       pub parallel: ParallelConfig,
       pub features: FeatureFlags,
   }

   pub fn validate_config(config: &ServingConfig) -> Result<ConfigSpec>;
   ```

2. **模板引擎**
   - 文件：`serving_agent/src/engine.rs`（新建）
   - 功能：Jinja2 模板渲染
   ```rust
   pub struct TemplateEngine {
       templates: HashMap<String, Template>,
   }

   impl TemplateEngine {
       pub fn render_project(&self, spec: &ConfigSpec, output_dir: &Path) -> Result<()>;
   }
   ```

3. **核心模板**
   - `templates/core/main.rs.j2`
   - `templates/backends/aclnn/ops.rs.j2`
   - `templates/backends/pypto/ops.rs.j2`
   - `templates/parallel/tensor_parallel.rs.j2`

4. **CLI 工具**
   - 文件：`serving_agent/src/main.rs`（新建）
   ```bash
   serving-agent generate --config config.toml --output ./my_server
   serving-agent validate --config config.toml
   serving-agent build --project ./my_server
   ```

#### 验收标准
- ✅ 可从配置生成可工作的推理服务器
- ✅ 生成代码可编译并运行 Qwen3-0.6B 推理
- ✅ 模板覆盖核心模块 70%
- ✅ 生成项目代码量 < 5000 行（可控）

#### 关键文件
- `serving_agent/config/spec.rs`（新建）
- `serving_agent/src/engine.rs`（新建）
- `serving_agent/src/main.rs`（新建）
- `serving_agent/templates/`（新建，多个 .j2 文件）

---

### Phase 4: 多机分布式支持（第 13-16 周）

**目标**：支持跨机器的分布式推理

#### 交付物

1. **分布式协调器**
   - 文件：`rust_llm_server/src/distributed/mod.rs`（新建）
   ```rust
   pub struct DistributedCoordinator {
       rank: usize,
       world_size: usize,
       peers: Vec<NodeInfo>,
       control_tx: mpsc::Sender<ControlMessage>,
   }

   impl DistributedCoordinator {
       pub async fn init(rank: usize, world_size: usize, master_host: &str, master_port: u16) -> Result<Self>;
       pub async fn barrier(&mut self, epoch: u64) -> Result<()>;
   }
   ```

2. **TCP 通信层**
   - 文件：`rust_llm_server/src/distributed/tcp.rs`（新建）
   - 功能：基于 TCP 的跨机器通信
   ```rust
   pub struct TcpTransport {
       connections: HashMap<usize, TcpStream>,
   }

   impl TcpTransport {
       pub async fn send_tensor(&self, dst_rank: usize, tensor: &DeviceTensor) -> Result<()>;
       pub async fn recv_tensor(&self, src_rank: usize) -> Result<DeviceTensor>;
   }
   ```

3. **多机模板**
   - `templates/communication/distributed.rs.j2`
   - `templates/parallel/pipeline_parallel.rs.j2`
   - `scripts/launch_cluster.sh.j2`

4. **启动脚本生成器**
   - 文件：`serving_agent/src/launcher.rs`（新建）
   - 功能：生成多机启动脚本

#### 验收标准
- ✅ PP=2 推理在 2 台机器上正确运行
- ✅ 分布式 barrier < 1ms
- ✅ 端到端延迟在单机的 110% 以内
- ✅ 节点故障检测与恢复

#### 关键文件
- `rust_llm_server/src/distributed/`（新建模块）
- `rust_llm_server/src/distributed/mod.rs`
- `rust_llm_server/src/distributed/tcp.rs`
- `serving_agent/templates/communication/distributed.rs.j2`
- `serving_agent/src/launcher.rs`（新建）

---

### Phase 5: PyPTO 性能优化（第 17-20 周）

**目标**：PyPTO 后端性能与 aclnn 持平

#### 交付物

1. **完整内核套件**
   - Flash Attention（带因果 mask）
   - MLP (SwiGLU)
   - RMSNorm
   - RoPE（旋转位置编码）
   - 量化算子（INT8/INT4）

2. **内核融合优化**
   - QK-Norm + RoPE 融合
   - SiLU + Mul 融合
   - LayerNorm 残差融合

3. **异步执行重叠**
   - 计算与通信重叠
   - 内核执行与数据传输重叠

4. **性能基准套件**
   - 文件：`benchmarks/qwen3_benchmark.rs`
   - 对比 aclnn vs PyPTO 性能

#### 验收标准
- ✅ Qwen3-8B 推理性能在 aclnn 的 95% 以上
- ✅ 内核编译时间 < 10s/层
- ✅ 内存占用在 aclnn 的 110% 以内
- ✅ 端到端延迟优化 > 20%（相比初始实现）

#### 关键文件
- `serving_agent/pypto_codegen/`（扩展示有代码）
- `rust_llm_server/src/ops/pypto.rs`（性能优化）
- `benchmarks/qwen3_benchmark.rs`（新建）

---

## 技术依赖与约束

### 必需依赖
- **Rust** 1.70+
- **PyPTO** modules/pypto（子模块，唯一后端）
- **Python** 3.9+（PyPTO 代码生成）

### 环境依赖
- **Ascend CANN** 7.0+
- **HCCL**（CANN 自带，多卡需要）

### 开发环境
- **Ascend NPU（910B）**：生产部署和性能测试

### 技术约束
- PyPTO 作为**唯一后端**
- 代码生成总量 < 10000 行（AI 可控）
- 生成的项目必须可独立编译部署
- **无 CUDA 依赖**

---

## 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| PyPTO 接口不稳定 | 高 | 中 | 版本锁定 + 抽象层隔离 |
| HCCL 多机兼容性 | 高 | 中 | 先支持 TCP 备选方案 |
| 性能不达标 | 中 | 低 | 分阶段优化，aclnn 回退 |
| 模板维护成本 | 中 | 中 | 保持模板简单，减少特性组合 |

---

## 成功指标

### 技术指标
- PyPTO 后端性能 ≥ aclnn 95%
- TP=4 扩展效率 > 70%
- 多机通信开销 < 10%
- 生成代码编译时间 < 2min

### 易用性指标
- 从配置到运行 < 5min
- 配置文件 < 50 行
- 文档覆盖率 100%

### 可维护性指标
- 模板代码复用率 > 80%
- 核心模块测试覆盖率 > 70%
- AI 生成时间 < 30s（单次请求）

---

## 交付物清单

### 代码交付
- [x] `rust_llm_server/src/ops/pypto.rs`（PyPTO 后端）
- [x] `rustBindings/hccl-sys/`（HCCL FFI）
- [x] `rustBindings/ascend/src/comm.rs`（HCCL 封装）
- [x] `rust_llm_server/src/distributed/`（多机协调）
- [x] `serving_agent/`（完整的 Agent 系统）

### 文档交付
- [x] Serving Agent 架构设计文档
- [x] 配置文件规范（TOML Schema）
- [x] API 接口文档
- [x] 部署指南

### 测试交付
- [x] 单元测试（覆盖率 > 70%）
- [x] 集成测试（单机/多机）
- [x] 性能基准测试
- [x] 端到端测试案例

---

## 近期优先级（前 8 周）

### P0（必须完成）
1. ✅ PyPTO ComputeOps 基础实现（Phase 1）
2. ✅ HCCL 通信基础（Phase 2）
3. ✅ 单机多卡 TP 验证（Phase 2）

### P1（高优先级）
1. ⚠️ Serving Agent 配置解析（Phase 3）
2. ⚠️ 核心模板集（Phase 3）
3. ⚠️ CLI 工具原型（Phase 3）

### P2（中优先级）
1. ⏳ 多机分布式原型（Phase 4）
2. ⏳ 性能优化（Phase 5）

---

## 附录：关键接口定义

### A. ServingConfig 示例

```toml
[model]
name = "qwen3"
variant = "8b"  # 0.6b | 4b | 8b
weights_path = "/data/models/qwen3-8b"

[hardware]
# PyPTO 后端（统一）
backend_type = "pypto"
device_id = 0  # NPU device_id

# Ascend NPU 配置
npus_per_node = 8
nodes = 2

[backend]
# PyPTO 后端配置
codegen_level = "tile"     # tile | block | op
use_cache = true           # 缓存编译内核
optimize_for = "latency"   # latency | throughput

[parallel]
tensor_parallel_size = 4
pipeline_parallel_size = 2

[features]
kv_cache = "paged"       # basic | paged
batching = "continuous"  # static | continuous
quantization = "none"    # none | int8 | awq-int4

# 分布式配置
[distributed]
master_addr = "192.168.1.1"
master_port = 29500
communication = "pypto"  # PyPTO TPUSH/TPOP
```

### B. PyPTO 内核接口

```rust
// PyPTO runtime FFI
extern "C" {
    // 执行 PyPTO 编译后的内核
    fn pypto_run(
        kernel_handle: *mut c_void,
        inputs: *const *const c_void,
        n_inputs: usize,
        outputs: *mut *mut c_void,
        n_outputs: usize,
        stream: *mut c_void,  // Ascend: aclrtStream
    ) -> i32;

    // 获取内核函数指针
    fn pypto_get_kernel_symbol(
        kernel_handle: *mut c_void,
        symbol_name: *const c_char,
    ) -> *mut c_void;
}
```

### C. PyPTO 通信接口

```rust
// PyPTO 通信器（支持单机和多机）
pub struct PyPTOComm {
    handle: *mut c_void,
    comm_type: PyPTOCommType,
}

// PyPTO TPUSH/TPOP 通信原语
extern "C" {
    // 发送数据到指定方向（Ring/Tree/Mesh 拓扑）
    fn pypto_push(
        tensor: *const c_void,
        size: usize,
        direction: u32,  // 0-7（8 个硬件方向）
        tag: u32,         // FIFO 标签（同步）
        stream: *mut c_void,
    ) -> i32;

    // 从指定方向接收数据
    fn pypto_pop(
        tensor: *mut c_void,
        size: usize,
        direction: u32,
        tag: u32,
        stream: *mut c_void,
    ) -> i32;

    // 初始化通信组
    fn pypto_comm_init(
        nranks: usize,
        rank: usize,
        comm_type: PyPTOCommType,
        master_addr: *const c_char,  // 多机需要
        master_port: u16,
    ) -> *mut PyPTOComm;
}
```

---

**文档版本**: v2.0
**最后更新**: 2026-03-25
**负责人**: Claude (Sonnet 4.5)
