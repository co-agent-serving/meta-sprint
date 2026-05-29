# Serving Agent 周报
2026-05-22 ~ 2026-05-29

---

## 一、Serving Agent 工作项

### P0-01 Serving 核心能力 & Qwen3-14B 单卡验证 · [meta-sprint#4](https://github.com/co-agent-serving/meta-sprint/issues/4)

- **进展（40%）**：Serving V2 多进程 NPU worker 框架合并，支持动态 batching 与 prefix cache，Qwen3-14B prefill 完成 chunked 重构并适配 fused JIT kernel（[pypto-serving#8](https://github.com/hw-native-sys/pypto-serving/pull/8) · [pypto-lib#403](https://github.com/hw-native-sys/pypto-lib/pull/403) · [pypto-lib#390](https://github.com/hw-native-sys/pypto-lib/pull/390) · [pypto-serving#14](https://github.com/hw-native-sys/pypto-serving/pull/14)）；KV cache block 管理完成统一重构，正修复 multi-batch decode block_table/slot_mapping 对齐问题（[pypto-serving#15](https://github.com/hw-native-sys/pypto-serving/pull/15) · [pypto-lib#408](https://github.com/hw-native-sys/pypto-lib/pull/408)）；发现 non-L3 decode_fwd 生成重复文本 bug，L3 decode_all 路径正确（[pypto-lib#396](https://github.com/hw-native-sys/pypto-lib/issues/396)）
- **下一步计划**：修复 non-L3 decode 路径正确性，完成 block_table 动态化，跑通端到端 benchmark 基线
- **责任人**：刘旭 @ndleslx · 许峰 @superxf · 郑左贺 @bumble0918 · （协同人 @lwDavid）

### P0-02 TurboQuant 开发 & Ascend 迁移可行性验证 · [meta-sprint#5](https://github.com/co-agent-serving/meta-sprint/issues/5)

- **进展（15%）**：TurboQuant KV Cache 压缩集成方案启动，初步 PR 已提交至 pypto-serving（[pypto-serving#6](https://github.com/hw-native-sys/pypto-serving/pull/6)）
- **下一步计划**：推进 TurboQuant kernel 在 PyPTO DSL 上的表达验证，确认数值对齐
- **责任人**：黄卓 @sunghajung6688

### P0-03 统一内存池基础 & Ascend 共享指针 + Engram 验证 · [meta-sprint#6](https://github.com/co-agent-serving/meta-sprint/issues/6)

- **进展（10%）**：本周无可见 issue/PR 活动，进度参考群聊
- **下一步计划**：确认SSD接口需求；接入serving框架验证
- **责任人**：黎亮 @LL-mixed 段诗锦 @sjduan

### P0-04/06 DeepSeek-V4 Decode + Prefill 单层调通 · [meta-sprint#7](https://github.com/co-agent-serving/meta-sprint/issues/7) · [meta-sprint#9](https://github.com/co-agent-serving/meta-sprint/issues/9)

- **Decode 侧进展（55%）**：——compressor 完成大量重构：per-batch start_pos、per-row RoPE、compressor_ratio128 cache contract 与 sparse_attn PA 布局对齐（[pypto-lib#351](https://github.com/hw-native-sys/pypto-lib/issues/351) · [pypto-lib#405](https://github.com/hw-native-sys/pypto-lib/pull/405) · [pypto-lib#402](https://github.com/hw-native-sys/pypto-lib/pull/402)）；compressor_ratio128 正推进全动态形状重构（[pypto-lib#410](https://github.com/hw-native-sys/pypto-lib/issues/410) · [pypto-lib#412](https://github.com/hw-native-sys/pypto-lib/pull/412)）；MTP 投影与 HC head 实现已合并，decode attention 精度修复完成（[pypto-lib#376](https://github.com/hw-native-sys/pypto-lib/pull/376)）；decode_indexer rope 与 score quant 融合到 matmul scope（[pypto-lib#401](https://github.com/hw-native-sys/pypto-lib/pull/401) · [pypto-lib#406](https://github.com/hw-native-sys/pypto-lib/pull/406)）；发现 decode_sparse_attn 短序列 bug（[pypto-lib#397](https://github.com/hw-native-sys/pypto-lib/issues/397)）。
- **Prefill 侧进展（25%）**——设计路径启动，新建 packed prefill metadata contract、dynamic prefill batching、decode KV cache paged metadata contract 三份设计 issue（[pypto-lib#382](https://github.com/hw-native-sys/pypto-lib/issues/382) · [pypto-lib#378](https://github.com/hw-native-sys/pypto-lib/issues/378) · [pypto-lib#383](https://github.com/hw-native-sys/pypto-lib/issues/383)）；prefill SWA attention、QKV RoPE tile、indexer compressor 实现已合并（[pypto-lib#399](https://github.com/hw-native-sys/pypto-lib/pull/399) · [pypto-lib#374](https://github.com/hw-native-sys/pypto-lib/pull/374) · [pypto-lib#384](https://github.com/hw-native-sys/pypto-lib/pull/384)）；prefill sparse attention 调优完成（[pypto-lib#394](https://github.com/hw-native-sys/pypto-lib/pull/394)）；dense HC tensor 用于 prefill SWA 的重构 PR 已提交（[pypto-lib#404](https://github.com/hw-native-sys/pypto-lib/pull/404)）
- **下一步计划**：Decode 侧重构 compressor_ratio128 动态形状、修复 sparse_attn 短序列 bug；Prefill 侧完成 metadata contract 定义，推进 var-len group batching
- **责任人**：杨耀东 @high-cloud · 郑左贺 @bumble0918 · 吴治锋 @wuzhf9 · 王成照 @zhaozhaozz · 段诗锦 @sjduan · （协同人 @wangqin1723-max · @zhangqi-chen · @lyfne123）

### P0-05 Rust Serving 框架重构：AscendC → PyPTO 后端 · [meta-sprint#8](https://github.com/co-agent-serving/meta-sprint/issues/8)

- **进展（10%）**：本周无可见 issue/PR 活动，方案待明确
- **下一步计划**：启动后端抽象层设计，确认 Rust 框架与 PyPTO backend 对接方案
- **责任人**：王明哲 @asanrocks

---

## 二、成员其他工作项

- **陈神爱 @hashiqiqixian**：实现 pypto 分布式 tensor subregion put 和跨 rank tensor read（[pypto#1567](https://github.com/hw-native-sys/pypto/pull/1567) · [pypto#1453](https://github.com/hw-native-sys/pypto/pull/1453)）
- **赵敏 @zmnobug**：推进 simpler 运行时调度器 stall 快照功能，完成选择性 tensor dump（[simpler#868](https://github.com/hw-native-sys/simpler/issues/868) · [simpler#872](https://github.com/hw-native-sys/simpler/pull/872)）
- **靳宗泉 @vegetabledoww**：开发 simpler Insight Trace 生成工具和统一 tensor/args dump 支持（[simpler#821](https://github.com/hw-native-sys/simpler/pull/821) · [simpler#792](https://github.com/hw-native-sys/simpler/pull/792)）
- **方竟志 @puddingfjz**：推进 simpler 远程 L3 worker，完成 Python callable 动态注册和分页注意力事件修复（[simpler#866](https://github.com/hw-native-sys/simpler/pull/866) · [simpler#839](https://github.com/hw-native-sys/simpler/pull/839) · [simpler#847](https://github.com/hw-native-sys/simpler/pull/847)）
- **王成照 @zhaozhaozz**：修复 MoE router 路由缓冲区 NPU 稳定性问题（[pypto-lib#255](https://github.com/hw-native-sys/pypto-lib/issues/255)）；提交 axonhub 请求日志筛选增强（[axonhub#1725](https://github.com/looplj/axonhub/pull/1725) · [axonhub#1723](https://github.com/looplj/axonhub/pull/1723)）