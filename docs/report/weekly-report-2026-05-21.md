# Serving Agent 周报
2026-05-14 ~ 2026-05-21

---

## 一、Serving Agent 工作项

### P0-01 Serving 核心能力 & Qwen3-14B 单卡验证 · [meta-sprint#4](https://github.com/co-agent-serving/meta-sprint/issues/4)

- **进展（30%）**：pypto-serving 仓库建立并完成 CI/模板配置 [pypto-serving#1](https://github.com/hw-native-sys/pypto-serving/pull/1) [pypto-serving#3](https://github.com/hw-native-sys/pypto-serving/pull/3)；Serving V2 多进程+动态批处理实现推进中 [pypto-serving#2](https://github.com/hw-native-sys/pypto-serving/pull/2)；Qwen3-14B RMS/LM head kernel 拆分重构完成 [pypto-lib#331](https://github.com/hw-native-sys/pypto-lib/pull/331)，spmd 和 mix 版本 decode 已合入 [pypto-lib#330](https://github.com/hw-native-sys/pypto-lib/pull/330)
- **下一步计划**：推进 Serving V2 PR 合入，完成 continuous batching + prefix cache 端到端验证
- **责任人**：刘旭 @ndleslx · 许峰 @superxf · （协同人 @lyfne123 · @xzhxzhxzh123 · @lwDavid）

### P0-02 TurboQuant PyPTO 开发 & 昇腾迁移可行性 · [meta-sprint#5](https://github.com/co-agent-serving/meta-sprint/issues/5)

- **进展（15%）**：TurboQuant KV Cache 压缩集成 PR 已提交，进入 review 阶段 [pypto-serving#6](https://github.com/hw-native-sys/pypto-serving/pull/6)
- **下一步计划**：完成 KV Cache 压缩集成，验证数值对齐，推进 TurboQuant 核心算子在 PyPTO DSL 上的表达
- **责任人**：黄卓 @sunghajung6688

### P0-03 统一内存池基础 & Ascend 共享指针 Engram 验证 · [meta-sprint#6](https://github.com/co-agent-serving/meta-sprint/issues/6)

- **进展（5%）**：工作项已创建并梳理关联仓库，UB 仿真平台上 OBMM 共享内存池 + Engram 已在 4/8 节点仿真中验证通过
- **下一步计划**：确认 Ascend 共享内存特性 API，启动 CPU/NPU 共享指针读写路径开发
- **责任人**：黎亮 @LL-mixed

### P0-04 DeepSeek-V4 decode 单层 PyPTO 拉通 · [meta-sprint#7](https://github.com/co-agent-serving/meta-sprint/issues/7)

- **进展（70%）**：DeepSeek-V4 decode 单层精度对齐已完成，本周集中进行性能优化——MoE routing 性能提升 [pypto-lib#323](https://github.com/hw-native-sys/pypto-lib/pull/323)、MoE EP=16 部署对齐 [pypto-lib#325](https://github.com/hw-native-sys/pypto-lib/pull/325)、shared expert tiling [pypto-lib#326](https://github.com/hw-native-sys/pypto-lib/pull/326)、sparse attention pack/quant 阶段优化 [pypto-lib#341](https://github.com/hw-native-sys/pypto-lib/pull/341) [pypto-lib#327](https://github.com/hw-native-sys/pypto-lib/pull/327)、compressor 并行流水线优化 [pypto-lib#342](https://github.com/hw-native-sys/pypto-lib/pull/342)、indexer decode 性能优化 [pypto-lib#343](https://github.com/hw-native-sys/pypto-lib/pull/343) 均已合入；MTP boundary 修复合入后 issue 已重新打开以跟踪剩余项 [pypto-lib#316](https://github.com/hw-native-sys/pypto-lib/issues/316)；prefill 和 MTP 实现跟踪 issue 已创建并提交 draft PR [pypto-lib#347](https://github.com/hw-native-sys/pypto-lib/issues/347) [pypto-lib#348](https://github.com/hw-native-sys/pypto-lib/issues/348) [pypto-lib#346](https://github.com/hw-native-sys/pypto-lib/pull/346)
- **下一步计划**：完成 compressor decode start position 修复，推进 prefill/MTP draft review，跟踪 compressor_ratio128 性能优化
- **责任人**：杨耀东 @high-cloud · 段诗锦 @sjduan · 吴治锋 @wuzhf9 · 王成照 @zhaozhaozz · 郑左贺 @bumble0918 · （协同人 @zhangqi-chen · @xzhxzhxzh123 · @wangqin1723-max · @lwDavid）

### P0-05 Rust Serving 框架重构：AscendC → PyPTO 后端 · [meta-sprint#8](https://github.com/co-agent-serving/meta-sprint/issues/8)

- **进展（10%）**：工作项已创建，Rust serving 框架基线（AscendC 后端）和 C/C++ serving 设计文档已就绪，后端抽象层重构尚未启动
- **下一步计划**：启动后端抽象层设计，在 feature branch 上进行 PyPTO 后端切换
- **责任人**：王明哲 @asanrocks

---

## 二、成员其他工作项

- **王成照**：修复 [pypto#1424](https://github.com/hw-native-sys/pypto/issues/1424) PTO 后端动态标量偏移 SSA 生成错误、[pto-isa#133](https://github.com/hw-native-sys/pto-isa/issues/133) CPU TRSQRT 临时变量命名错误
- **杨耀东**：报告并跟踪多个 pypto 编译器 bug（[pypto#1415](https://github.com/hw-native-sys/pypto/issues/1415) [pypto#1402](https://github.com/hw-native-sys/pypto/issues/1402) [pypto#1370](https://github.com/hw-native-sys/pypto/issues/1370)），涉及 tile valid_shape 丢失、transpose scratch、out-window 名称冲突
- **方竟志**：修复 [pto-isa#122](https://github.com/hw-native-sys/pto-isa/issues/122) CPU 后端 TPUT_IMPL 拷贝方向错误；推进 [simpler#537](https://github.com/hw-native-sys/simpler/pull/537) AICPU 启动迁移到 rtsLaunchCpuKernel + 零部署调度器；review [simpler#817](https://github.com/hw-native-sys/simpler/pull/817) 动态 CommDomain 分配、参与 [simpler#752](https://github.com/hw-native-sys/simpler/pull/752) 多通信域支持
- **靳宗泉**：开发 [simpler#821](https://github.com/hw-native-sys/simpler/pull/821) Insight Trace workspace 生成，支持 MindStudio profiling
- **赵敏**：开发 [simpler#801](https://github.com/hw-native-sys/simpler/pull/801) 为 tensor dump 添加运行时参数记录