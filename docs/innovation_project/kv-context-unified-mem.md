**KV-Context统一内存**

### 1. 项目目的

随着大规模推理服务投入代码生成等长上下文实际应用，内存管理已成为核心瓶颈。当前推理服务面临两个相互交织的内存挑战：**推理层面的 KVCache 压力**（长序列生成时 KVCache 随序列长度线性增长）和 **Agent 系统层面的上下文内存爆炸**（多轮对话累积的上下文迅速超出模型固定窗口）。这两个问题通常被分开处理——推理系统关注 KVCache 的高效存储与访问，Agent 系统关注外部记忆的检索与注入。然而，它们在结构上是同一问题：如何在延迟约束下，将异构信息调度到有限的 GPU 内存中。本项目提出**统一的多层级内存管理架构**，将 KVCache 和 Agent 上下文纳入同一调度框架，覆盖从 NPU/GPU 高带宽内存（HBM）到 CPU DRAM 再到持久化存储的完整内存层次。

### 2. 已有工作

KVCache 管理。 PagedAttention [1] 将虚拟内存分页引入 KVCache，实现非连续存储，大幅降低碎片。Mooncake [2] 提出以 KVCache 为中心的分离式推理架构，已集成至 vLLM 并支持 Ascend。Jenga [3] 针对异构嵌入维度设计两级分配器。PagedEviction [4] 提出结构化块级驱逐算法。PAM [5] 协调异构 PIM 内存设备。多篇综述 [6-8] 从存储布局、生命周期等维度系统梳理了该领域。

Agent 上下文内存管理。 MemGPT [9] 借鉴操作系统分层内存思想，通过上下文内外分页使 LLM 处理超长对话。HyMem [10] 提出双粒度存储与动态双层检索，降低计算成本 92.6%。Pancake [11] 为多 Agent 场景设计统一层次内存系统。最新工作 MemArt [12] 以 KVCache 为中心存储 Agent 记忆，在隐空间通过注意力检索，显著减少预填充 token。两篇综述 [13,14] 提供了统一分类法。

研究缺口。 现有工作分别优化推理 KVCache 或 Agent 上下文，未解决两者在 GPU 内存中实时竞争的联合调度问题。Pancake 处理多 Agent KVCache 层次但无统一代价模型；MemArt 仅改变表示层而未涉及资源调度。本项目首次提出联合效用调度框架，统一管理两类内存。

### 3. 创新思路

核心贡献是一个**统一的多层级内存管理架构**，包含以下三项创新：

**创新一：统一内存抽象层（UMB）。** 设计**统一内存块（Unified Memory Block, UMB）** 作为 KVCache 块（来自分页注意力机制）和 Agent 上下文块（来自 MemGPT 式虚拟上下文）的共同抽象。每个 UMB 包含：（1）元信息——来源类型、语义重要性分数、访问频率、最后访问时间；（2）指向当前存储层实际数据的指针；（3）状态标志——当前所在层级及持久化需求。该抽象消除了两个领域间的语义鸿沟，使单一内存管理器能够统一调度两者。与 MemArt [19] 不同（后者仅将 KV 格式作为 Agent 内存的表示选择），UMB 是基于代价而非格式做出层级迁移决策的调度原语。

**创新二：联合效用内存调度。** 传统方法独立决策：KVCache 驱逐基于访问模式（如 LRU），Agent 上下文交换基于重要性分数。本创新是**联合效用代价-收益调度器**，同时跨两类块做出驱逐和迁移决策。对于每个待驱逐的 UMB，调度器计算统一的效用分数，综合：（1）**重用潜力**——该 KVCache 块在后续注意力计算中被需要的概率，基于注意力历史模式估计；（2）**检索可能性**——该 Agent 上下文块在后续推理中被查询的概率，基于记忆检索统计。调度器在全局范围内选择，以最小化期望缺失代价。借鉴 HyMem 的双层检索思想和 Jenga 的 LCM 分配策略，算法还根据工作负载阶段（如 Agent 规划阶段优先分配上下文块）动态调整 GPU 中两类内存的容量配比。

**创新三：任务计划驱动的 KVCache 预取。** 标准 KVCache 预取是被动的：请求到达时才加载块。我们提出**任务计划驱动的主动预取**，将内存管理从被动响应升级为主动预测。Agent 的任务规划器输出后续 N 步推理的**子任务列表**。内存管理器解析该列表，将每个子任务映射到最可能需要的 KVCache 块和上下文块（基于历史访问模式），并在步骤执行前将其预加载到 GPU HBM。规划器与内存管理器之间的接口是轻量级的**预取提示**（子任务 ID、估计 token 范围、相关范围），无需修改模型本身。借鉴 MemGPT 的事件驱动架构和 Pancake 的多级索引缓存，该机制降低了步骤边界的冷启动缺失率，在代码审查或多文件重构等结构化 Agent 工作流中尤为有效。

### 4. 预期成果

**交付成果。** 完成统一多层级内存管理架构的设计与实现，包括 UMB 抽象层、联合效用调度器和任务计划驱动的预取机制。代码支持集成 Qwen 系列模型（Ascend NPU 环境）及开源 Agent 框架（如 Letta、自定义工具调用 Agent）。

**评估指标与基线。** 在 Qwen 系列模型、Ascend NPU 环境下评估，测试场景包括单轮长文档分析、多轮对话 Agent 以及混合 KVCache 压力与上下文增长的复杂推理任务。基线为 vLLM（无统一管理）和 Pancake（最优已有系统级工作）。相比基线的目标提升：

- **端到端推理吞吐量：** 相比 vLLM 提升 ≥30%
- **长序列推理的峰值 GPU 内存：** 相比 vLLM 降低 ≥40%
- **多轮 Agent 任务中的上下文切换延迟：** 相比 vLLM 降低 ≥50%
- **长对话任务准确率保持：** 相比无限上下文基线，下降 ≤5%

### 参考文献

[1] PagedAttention: Efficient Memory Management for Large Language Model Serving with PagedAttention. SOSP, 2023.

[2] Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot. FAST, 2025. (Best Paper Award)

[3] Jenga: Effective Memory Management for Serving LLM with Heterogeneity. SOSP, 2025.

[4] PagedEviction: Structured Block-wise KV Cache Pruning for Efficient LLM Inference. EACL, 2026.

[5] PAM: Processing Across Memory Hierarchy for Efficient KV-centric LLM Serving System. arXiv, 2026.

[6] A Survey on Large Language Model Acceleration based on KV Cache Management. arXiv, 2025.

[7] Towards Efficient Large Language Model Serving: A Survey on System-Aware KV Cache Optimization. TechRxiv, 2025.

[8] Efficient KV Cache Management in Large Language Model Serving: A Lifecycle-Oriented Survey. HKUST-GZ, 2025.

[9] MemGPT: Towards LLMs as Operating Systems. arXiv, 2023.

[10] HyMem: Hybrid Memory Architecture with Dynamic Retrieval Scheduling. arXiv, 2026.

[11] Pancake: Hierarchical Memory System for Multi-Agent LLM Serving. arXiv, 2026.

[12] MemArt: KVCache-Centric Memory for LLM Agents. ICLR, 2026.

[13] Rethinking Memory Mechanisms of Foundation Agents in the Second Half: A Survey. arXiv, 2026.

[14] LLM Agent Memory: A Survey from a Unified Representation–Management Perspective. 2026.