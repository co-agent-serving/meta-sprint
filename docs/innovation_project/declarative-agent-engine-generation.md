## 基于AI的声明式Agent及推理引擎生成

### 1. 项目目的

当前构建具备Agent能力的大语言模型服务系统面临三大痛点：

一是高性能推理引擎开发复杂度高，与硬件深度绑定，新模型迁移成本居高不下。以vLLM为例，其代码量达数万行，且与NVIDIA硬件强耦合。模型架构的快速演进（MoE、MLA、多模态等）不断催生新算子和新调度策略，但这些优化被回合到通用框架后往往无法跨模型复用，导致框架持续膨胀。与此同时，为覆盖海量场景而积累的调优选项极大扩张了配置空间，新模型达到生产级性能仍需N人月的专家调优。

二是Agent框架与推理引擎之间缺乏深度融合，二者以黑盒方式交互。当前LangChain等框架仅通过API调用推理服务，Agent的上下文管理、记忆策略与推理引擎的KV Cache、批处理调度完全割裂。Agent无法向推理层传递语义信息（如对话状态、工具调用意图），推理层也无法基于Agent行为特征进行针对性优化，导致显存资源挤占和调度效率损失，形成双重性能瓶颈。

三是不同形态的Agent应用对推理服务的要求差异巨大，单一调优规则难以覆盖。Agent应用在控制流确定性、记忆模式、工具调用、部署拓扑、任务时间尺度等多个维度上呈离散分布——客服分流、代码助手、深度研究、社交模拟等典型场景对批处理、KV Cache、调度优先级的最优配置截然不同。通用框架以一套静态参数覆盖全部坐标，必然以特定场景性能折损为代价，新场景上线仍需重启N人月的专家调优循环。

本项目的根本思路是打破这种局面：**不再依赖通用推理框架的后验式适配，而是直接面向目标模型与目标场景，构建一个由AI驱动的多级代码生成系统**。开发者只需用自然语言或高层声明描述需求（模型规格、推理场景、Agent行为、工具集等），系统便自动生成将推理引擎与Agent运行时框架集成的一体化服务代码。与传统方法不同，生成的推理引擎不依赖现有臃肿的推理框架，而是直接对接PyPTO/Triton/TileLang等kernel DSL层算子生成工具。通过分层生成（高层Agent逻辑 → 中层调度与内存管理 → 底层kernel DSL调用），实现从算子到Agent服务的完整自动化链路，并通过迭代优化持续适应负载与新硬件，从根本上解决模型生态迁移中的适配与调优痛点。

### 2. 已有工作

**推理引擎**。vLLM、SGLang 等需手写数万行框架代码，vLLM 最新 Model Runner V2（MRV2，2026）通过模块化重构将调度与模型逻辑解耦，实现 56% 吞吐提升 [1]，但仍是手工编码并绑定 NVIDIA 硬件，未触及 Agent–推理深度融合。

**Agent框架与声明式规范**。LangChain 等以 API 黑盒方式调用推理服务 [2]。Auton Framework 提出 AgenticFormat 声明式规范，实现 Agent 定义与执行解耦 [3]，但其规范仅覆盖 Agent 行为，不涉及推理引擎配置——这正是本项目 DSL 的扩展空间。

**AI驱动的算子与系统生成**。英伟达 AVO [4] 在 B200 上自主优化注意力算子 7 天，BF16 下达到 1668 TFLOPS，超越 cuDNN 3.5%、FlashAttention-4 10.5%；Design Conductor 2.0 [5] 用多智能体在 80 小时内构建出支持 TurboQuant 的 LLM 推理加速器；ParEVO [6] 用进化型智能体优化并行算法，在 ParEval 上获 106× 加速。这些工作证明 AI Agent 可在单算子或单加速器粒度上自主进化，但都未涉及推理服务层面的多组件协同。

**AI驱动的代码生成与自进化**。Autopoiesis [7] 在运行时动态合成 Serving Policy 代码，应对负载波动获得 34% 性能提升，直接验证了 LLM 驱动 serving 代码生成的可行性；SelfEvolve [8] 实现 Agent 对自身代码的运行时生成与进化；DSL-Monkeys [9] 通过自生成示例提升 LLM 在 TileLang 等新兴 DSL 上的生成能力。但 Autopoiesis 仅生成运行时策略片段，缺少跨层静态全栈生成能力。

**研究缺口**。综上，现有工作在"单算子/单加速器自演化"与"运行时策略片段生成"两端各有突破，但都未覆盖**面向具体模型与场景的Agent–推理一体化全栈生成**。本项目的核心贡献正是填补这一缺口：在构建时基于声明式输入静态生成推理-服务-应用全栈代码，并支持离线再生成式的持续演进。

### 3. Agent应用场景与推理需求差异

为了让系统能够针对不同Agent形态生成最优的推理服务配置，我们引入一个**面向推理服务的5维Agent分类框架**，作为后续创新点的对齐锚点：

| 维度 | 取值 | 对推理服务的影响 |
|------|------|----------------|
| **D1: 控制流确定性** [11] | Workflow（预定义路径，含Routing/Prompt-chaining/Parallelization等）/ Agent（动态决策，含ReAct/Reflexion等）/ 混合 | Workflow可激进prefix caching与工具链预编译；Agent难缓存但可基于规划信号驱动预取 |
| **D2: 记忆模式** [13] | 短窗口（仅当前会话）/ 长上下文（全量保留）/ 摘要+外部存储（向量库+召回） | 决定KV Cache策略：页大小、量化精度、是否持久化到二级存储 |
| **D3: 工具调用模式** | 无 / 单步 / 多步串行 / 多步并行（fork-join） | 决定批处理粒度、调度优先级、是否支持并发子请求 |
| **D4: 部署拓扑** [12] | 单Agent / Star（中心编排）/ Chain（SOP流水线）/ Mesh（多Agent对称协作） | 决定服务实例数、跨Agent KV共享、热点路由 |
| **D5: 任务时间尺度** | Short-horizon（秒级）/ Medium-horizon（分钟级，多轮对话）/ Long-horizon（小时/天级持续任务） | 决定KV Cache生命周期管理、量化持久化触发条件、是否启用checkpoint机制 |

**典型场景的5维坐标与推理优化对应**：

| 场景 | D1 | D2 | D3 | D4 | D5 | 推荐优化组合 |
|------|----|----|----|----|----|------------|
| 客服分流系统 | Workflow-Routing | 短窗口 | 单步 | Star | Short | 激进prefix caching、工具链预编译、大批次合并 |
| 代码助手（Cursor/Cline类） | Agent (ReAct) | 长上下文 | 多步串行 | 单Agent | Medium | 长上下文KV量化、小批次保延迟、规划驱动预取 |
| 研究型Deep Research | Agent (Plan-Execute) | 摘要+外部存储 | 多步并行 | Star | Long | KV量化持久化、fork-join批处理、checkpoint恢复 |
| 软件团队协作（MetaGPT类） | Workflow-Chain | 摘要+外部存储 | 多步串行 | Chain | Medium | SOP阶段prefix复用、阶段间KV切换、流水线并行 |
| AI社交模拟（AI Town类） | Agent (Reflexion) | 摘要+外部存储 | 多步并行 | Mesh | Long | 跨Agent KV共享、对称负载均衡、低频对话压缩 |

这一框架揭示了一个核心事实：一个真实的Agent应用是5维空间中的一个具体坐标点，而非"Agent"这一笼统标签。通用推理框架以静态调优覆盖如此广阔且离散的坐标空间，必然以性能折损为代价；这也是本项目主张**面向具体场景按需生成**的根本依据。

### 4. 创新思路

**创新一：面向Agent–推理一体化的多级代码生成方法**

- **现状**：vLLM/SGLang 等通用框架以数万行手写代码覆盖所有模型与硬件，新模型迁移需 N 人月专家调优；高层 Python 框架与 AscendC/CCE 底层算子之间是黑盒调用关系，无法跨层传递优化语义。
- **问题**：模型架构持续演进（MoE/MLA/Mamba/扩散/多模态）使通用框架不断膨胀，同时 Agent 行为层、推理调度层、算子层各自为政，优化只能局部进行，无法端到端协调。
- **关键技术**：分层代码生成流水线，将自然语言或高层 DSL 自动翻译为可直接部署的服务代码。流水线包含三个中间表示层，各层通过结构化 IR 接口衔接：
  - *Agent 行为层 IR*：描述工具调用协议（输入/输出 schema、调用频率约束）、记忆策略（短窗口/摘要+外部存储/全量保留）、规划模式（ReAct/Plan-Execute/Reflexion），并显式标注 D1–D5 坐标，作为下游决策的锚点。
  - *推理调度层 IR*：接收行为层 IR 中的 D1–D5 坐标与模型规格，生成批处理策略（连续/动态批处理、batch 上限）、KV Cache 配置（页大小、量化精度、滑动窗口宽度）、分布式方案（TP/PP 划分、rank 间通信拓扑）。该层输出一份结构化的调度参数表，供运行时层直接消费。
  - *算子对接与运行时层 IR*：根据调度层的参数表与模型的算子组合图，选择合适的 kernel DSL（PyPTO/Triton/TileLang/Torch），决定每个算子的调用粒度——是大颗粒调用已有 Attention module，还是生成 Tile 级细粒度融合子图（与创新三配合）。
  
  系统不生成 AscendC/CCE 等底层硬件算子，而是生成”组装逻辑”——将高层框架代码与 kernel DSL 代码组合为完整服务。kernel DSL 以 Python 呈现，与模型框架代码处于同一语义平面，AI 可在统一抽象层级完成跨层生成，硬件亲和性由后端编译器保证。

  *为何必须用 AI 而非模板/编译器*：(1) 模型架构离散且快速演进，模板要么覆盖不全，要么膨胀成又一个 vLLM，AI 可理解模型结构语义并组合已知优化模式；(2) 自然语言意图隐含上下文（如”客服场景”≈路径固定+工具集合小+对话短），AI 可借领域知识展开为 D1–D5 坐标；(3) Agent 层语义（如”工具调用结果 3 轮后被复用”）需穿透到调度层（提升 KV Cache 块保留优先级）与算子层（避免激进量化），这种 3–4 层语义穿透是规则系统无法表达的。
- **挑战**：(1) *LLM 在新架构上的泛化*——训练语料未覆盖的新架构（如 Mamba 早期）可能导致生成错误，需借助 few-shot 示例、约束解码与人工审核补足；(2) *IR 语义完备性*——行为层意图能否被无损翻译到调度与算子层，取决于 IR schema 的覆盖度，schema 设计遗漏会导致语义丢失；(3) *生成代码的正确性验证*——需配套沙盒编译、单元测试、性能回归三重验证。

**创新二：面向场景与模型的智能优化策略自动选择**

- **现状**：通用框架中批处理策略、KV Cache 设计、分布式配置等优化相互隔离，分别调优的人力成本极高，且调优结果仅适用于特定模型+硬件组合。
- **问题**：第 3 节揭示 Agent 应用在 5 维空间中分布广泛且离散，通用框架的”一刀切”调优无法兼顾如此异构的应用画像；跨层参数间存在隐性依赖（如 TP 度影响 KV Cache 分片策略），传统逐层调优无法捕捉。
- **关键技术**：AI Agent 接收第 3 节定义的 5 维 Agent 坐标与模型规格，自动选择并组合跨层优化策略。决策覆盖三个层面：
  - *推理侧 — 按 Agent 坐标映射*：将 D1–D5 坐标组合映射为具体的参数配置。例如 D1=Workflow-Routing + D2=短窗口 → 激进 prefix caching（共享前缀占比阈值 ≥ 60%）+ 工具链预编译 + 大批次合并（batch 上限 256）；D1=Agent(ReAct) + D2=长上下文 → 长上下文 KV 量化（FP16→INT8）+ 小 batch 保延迟（上限 8）+ 规划驱动的 KV 预取（基于 ReAct 观察-思考-行动循环预加载下轮可能用到的 KV 块）。
  - *Agent 框架侧 — 运行时形态选择*：D1=Workflow 主导时生成有限状态机（FSM）式执行器，路径可静态分析，便于 prefix caching 等编译期优化；D1=Agent 主导时生成事件循环式动态调度器，支持工具动态发现与决策回滚；混合场景下生成分段架构——确定性段走 FSM、探索性段走动态调度，通过统一上下文接口交接。
  - *分布式部署 — 跨层联合决策*：输入模型参数量（如 70B/405B）、可用硬件规格、D3 工具调用模式（fork-join 并发度 vs 串行），联合输出 TP/PP 划分、rank 间通信拓扑、并发子请求调度优先级。例如 MoE 模型 + 长上下文 + D3=多步并行时，AI 先验”专家在 TP 维度切分通常优于 PP”可跳过大量无效组合，直接收敛到 TP=专家数×冗余度的高效方案。

  *为何需要 LLM 而非传统搜索/规则引擎*：(1) 跨层隐性依赖使参数空间指数爆炸（TP × batch × KV page × 并发度），LLM 可通过语义先验压缩搜索空间；(2) 用户意图模糊（”低延迟”是 <100ms 还是 <10ms？），LLM 可通过领域知识与追问消解，并自动展开”客服场景”为 D1–D5 坐标。
- **挑战**：(1) *策略组合的语义覆盖度*——LLM 的先验知识可能遗漏某些有效的参数组合，需持续积累策略库与 few-shot 示例；(2) *LLM 选错策略的兜底*——通过约束解码限制输出到合法策略范围、沙盒验证性能不劣化于默认配置、保留 fallback 至默认策略的能力。

**创新三：面向场景化 / 特定形状的融合子图生成策略**

- **现状**：通用推理框架（如 vLLM）在设计时需权衡各种输入形状和硬件规格，算子边界固定——serving 和 model 层均为 Python，算子以 `torch.ops.xx` 暴露，底层由 AscendC 算子库实现，对框架完全黑盒。
- **问题**：通用性以牺牲特定场景性能为代价。例如 batch=1 + seq<2048 的小请求场景下，通用 Attention kernel 的 tensor core 启动开销占比过高；RoPE+Attention 等本可融合的算子因边界固定被迫独立调用，产生不必要的显存读写。
- **关键技术**：AI Agent 根据用户声明的部署场景（batch size、sequence length 范围、模型结构）自动调整算子实现策略：
  - *形状驱动的计算路径选择*：当 batch ≤ 4 且 seq ≤ 2048 时，Attention/KVCache 各维度 tensor 较小，tensor core 启动的固定开销和 vector-cube 切换代价占比过高。系统自动选择全程 vector 计算路径，规避 cube 单元启动开销。该决策由形状分析模块完成：提取模型计算图中各算子的输入 tensor 形状，结合硬件的 vector/cube 启动阈值，生成路径选择条件编译到 kernel DSL 代码中。
  - *融合算子按需生成*：Agent 在 Python 语义平面上扫描模型计算图，识别可融合的算子对/链。典型融合模式包括：RoPE + Attention（位置编码可内联到 Attention 计算，节省一次显存读写）、MoE Router + Expert Compute（batch 较大时可合并路由与专家计算，减少 dispatch 开销）、LayerNorm + Residual + Attention（Pre-LN 结构可三合一）。Agent 根据场景形状决定是否启用每种融合模式（如 batch=1 时 RoPE+Attention 融合收益有限，不融合反而更优），然后用 PyPTO/Triton/TileLang 等 kernel DSL 生成融合后的算子代码，由后端编译器转换为硬件指令。
- **挑战**：(1) *融合正确性验证*——融合后的算子语义必须与原始算子链严格等价，需数值精度回归测试（对比融合前后输出误差 < 1e-5）；(2) *形状分析精度*——动态 shape（如 batch 大小波动）可能使静态选择的路径在运行时次优，需要 shape 分桶策略或运行时 fallback 机制。

**创新四：Agent上下文与LLM KVCache的统一内存协同管理**

- **现状**：推理引擎的 KVCache 与 Agent 的记忆上下文独立管理——KVCache 由推理引擎的分页/滑动窗口策略控制，Agent 记忆由框架层的向量库或摘要模块管理，二者互不感知。
- **问题**：在长上下文 Agent 场景下，两类内存需求同时消耗有限的 NPU 显存并相互挤占。FP16 下仅 3 个 Agent 即可占满 10.2GB 缓存预算 [10]，而框架无法根据语义重要性做全局取舍，只能按各自局部策略驱逐，导致高价值上下文被误淘汰或显存利用率低下。
- **关键技术**：将 KVCache 块与 Agent 外部记忆块纳入统一调度框架，共享同一套代价-收益模型：
  - *Agent 行为驱动的预取*：依据 Agent 对话状态和任务规划信号预判下一轮推理的信息范围。例如 D1=Agent(ReAct) 场景中，当前处于”思考”阶段且规划显示下一步将调用搜索工具，则预加载该工具历史返回值的 KV 块。预取触发条件由行为层 IR 中标注的 D1–D5 坐标决定：D1=Workflow 时基于路径可达性做确定性预取，D1=Agent 时基于规划概率做启发式预取。
  - *统一代价-收益模型*：每个内存块（无论 KVCache 还是 Agent 记忆）维护一个调度评分 = 复用概率 × 重算成本 × 语义权重。复用概率由历史访问模式与 Agent 状态转移概率估算；重算成本对 KVCache 块为重新 prefill 的计算量，对 Agent 记忆为外部存储的 I/O 延迟；语义权重由行为层标注的重要性（如系统 prompt > 工具返回值 > 中间推理）决定。当 NPU 显存紧缺时，按评分全局排序做驱逐/迁移决策。
  - *量化与持久化*：借鉴 [10] 的 Q4 持久化方案，当块评分低于持久化阈值时触发 FP16→4-bit 量化并写入二级存储（昇腾 HBM 外挂 SSD/NVMe），量化后可承载 4 倍上下文。加载时反量化回 FP16，引入一次解码精度损失但避免重新 prefill 的高昂成本。量化触发条件由 D2（记忆模式）与 D5（时间尺度）联合决定：D2=长上下文 + D5=Long-horizon 时更早触发量化，D2=短窗口时无需量化。
- **挑战**：(1) *代价模型精度*——复用概率与语义权重的估算依赖 Agent 行为的预测准确性，行为不确定时模型可能误判；(2) *量化精度与推理质量权衡*——4-bit 量化引入的精度损失在长链推理中可能累积，需针对不同模型和场景标定可接受的量化阈值。

**创新五：基于用户画像与模型替换的全栈自演进机制**

- **现状**：构建时一次性生成的服务代码无法适配后续变化；传统方案中模型替换需重新进行 N 人月专家调优（重新校准批处理、KV Cache、并行策略、算子融合）。
- **问题**：用户的真实负载特征会随时间漂移（请求长度分布、并发模式、工具调用频次等），且企业一体机用户常需在同一昇腾硬件上替换底层模型（如 DeepSeek-V4 → GLM → MiniMax），二者都要求服务代码持续适配。
- **关键技术**：继承 AVO [4] 和 SelfEvolve [8] 的自演进思想，但将演进路径限定为**离线再生成**而非运行时自变异，在保留演进能力的同时规避运行时可控性与安全性风险：
  - *基于用户画像的策略自演进*：系统持续收集架构级指标（吞吐 P99 延迟、NPU 显存占用率、KV Cache 命中率、批处理填充率、请求长度分位数），按时间窗口（如每小时/每天）聚合形成负载画像（如"白天 70% 客服 Routing + 30% 代码助手长上下文；夜间 90% 离线批处理"）。漂移检测模块计算当前画像与上次生成画像的分布距离（如 KL 散度），超过阈值时触发离线再生成：将新画像作为 DSL 输入的补充约束，重新执行创新一的多级生成流水线，产出新版服务代码，通过灰度发布（5%→20%→100% 流量切换）平滑上线。
  - *面向模型替换的全栈自演进*：用户更换底层模型时，系统接受新模型的规格描述（参数量、架构类型、算子组合图），在保持硬件配置和 Agent 场景描述不变的前提下，自动重新执行创新一至创新三的生成流程：重新分析算子组合 → 重新选择优化策略 → 重新生成融合子图。将模型替换的工程成本从 N 人月降至小时级。
  - *多版本演化与时段切换*：基于负载画像的分时特征，系统可同时维护多个演化分支（如"低延迟版"与"高吞吐版"），并根据时段或外部信号自动切换部署版本。各版本均为经过完整验证的静态代码，运行时无 LLM 参与。
- **挑战**：(1) *漂移检测阈值标定*——阈值过敏感会导致频繁触发再生成（浪费算力），过迟钝则性能长期偏离最优，需结合业务 SLA 自适应调整；(2) *再生成版本的回归验证*——新版代码必须通过功能正确性、性能不劣化、显存不溢出三重验证后才能上线，验证流程本身的设计成本不可忽视。

### 5. 预期成果与评估指标

**总体指标（项目级）：**

- **示例应用 ≥ 3 个**，覆盖不同 D1–D5 坐标：
  - *中软推理集群弹性调优*（Workflow-Routing / 短窗口 / Short）——验证创新5用户画像驱动的离线再生成。
  - *一体机长对话与代码助手*（Agent-ReAct / 长上下文 / Medium）——验证创新4统一内存调度。
  - *推理加速算法昇腾迁移*——选取 TurboQuant、SparseAttention 等 NVIDIA 侧成熟算法，通过本系统跨层级自动迁移到昇腾，验证创新1–3端到端能力。
- **模型迁移耗时**：从 N 人月 → 小时级（基线：vLLM 适配 DeepSeek/MoE 类新架构典型 3–6 人月专家工作量）。
- **全栈服务性能**：在 Ascend NPU 上达到手写优化基线（vLLM-Ascend 或华为内部手调实现）的 80% 以上。可达性依据：AVO [4] 单算子层面已超越 cuDNN 3.5%、FA4 10.5%，验证 AI 驱动生成可达手写水平。
- **NL→DSL 转换准确率 ≥ 80%**：用户自然语言被正确翻译为含 D1–D5 坐标、模型规格、工具集的 DSL，且下游创新一可基于该 DSL 生成可编译运行的代码。

**分创新点验收：**

| 创新点 | 验收指标 | 基线/可达性依据 |
|---|---|---|
| **创新1** 多级代码生成 | 生成代码可编译运行率 ≥ 90%；三层 IR schema 覆盖 Dense / MoE / MLA / 多模态四类架构 | DSL-Monkeys [9] 验证 LLM 在 TileLang 等新兴 DSL 上的生成可达性 |
| **创新2** 策略自动选择 | *不劣化兜底*：选中策略性能 ≥ 默认配置的请求占比 100%；*场景化收益*：典型场景（长对话/低延迟/高吞吐）端到端延迟或吞吐量相比默认配置提升 ≥ 30% | vLLM 公开 benchmark 中默认配置 vs 最优手调配置的差距区间 20–50% |
| **创新3** 融合子图 | 融合算子与原算子链数值精度误差 < 1e-5（FP16）；batch ≤ 4 且 seq ≤ 2048 的小形状场景相对通用 kernel 提升 ≥ 20% | 小形状下 tensor core 启动开销占比超 30%，场景化裁剪可基本消除该开销 |
| **创新4** 统一内存协同 | 同 NPU 显存预算下并发 Agent 数 ≥ 2×；长上下文（≥ 32K）单请求 TTFT 下降 ≥ 50%；统一代价模型驱逐决策与人工策略命中偏差 ≤ 10% | [10] 报告 Q4 量化可承载 4× 上下文，本项目叠加统一调度后保守目标 2× |
| **创新5** 用户画像与模型替换自演进 | 离线再生成端到端耗时 ≤ 4 小时（含 DSL 重写、代码生成、回归测试、灰度切换）；漂移检测召回率 ≥ 85% 且误触发率 ≤ 5%；模型替换后端到端性能达原模型基线 90% 以上 | 经验阈值，依业务 SLA 校准；模型替换基线参考创新一至三完整生成流程的复用 |

### 6. 参考文献


[1] vLLM Team. Model Runner V2: A Ground-Up Re-implementation of vLLM. vLLM Blog, March 2026. [Online]. Available: https://blog.vllm.ai/2026/03/01/mrv2.html

[2] LangChain Blog. LangChain and LangGraph Agent Frameworks Reach v1.0 Milestones. 2025. [Online]. Available: https://blog.langchain.com/langchain-langgraph-1dot0

[3] Auton Agentic AI Framework. AgenticFormat Standard: Declarative Agent Schemas. arXiv:2602.23720, February 2026. [Online]. Available: https://arxiv.org/abs/2602.23720

[4] Chen, T., Xu, B., Ye, Z., et al. AVO: Agentic Variation Operators for Autonomous Kernel Evolution. arXiv, 2026.

[5] Suresh Krishna, R., Chin, D., et al. Design Conductor 2.0: An agent builds a TurboQuant inference accelerator in 80 hours. arXiv:2605.05170, 2026.

[6] Liu, Q. C. ParEVO: Agentic Evolutionary Synthesis of Parallel Algorithms for Irregular Data. 2026.

[7] Jiang, Y., et al. Autopoiesis: A Self-Evolving System Paradigm for LLM Serving Under Runtime Dynamics. arXiv:2604.07144, 2026. [Online]. Available: https://arxiv.org/abs/2604.07144

[8] Robol, M. Self-Evolving Software Agents. arXiv:2604.27264, 2026.

[9] Liu, C., Geng, R., et al. DSL-Monkeys: Self-Generated In-Context Examples for Low-Resource DSL Code Generation. OpenReview, 2026.

[10] Shkolnikov, Y. P. Agent Memory Below the Prompt: Persistent Q4 KV Cache for Multi-Agent LLM Inference on Edge Devices. arXiv:2603.04428, 2026.

[11] Anthropic. Building Effective Agents. Anthropic Engineering Blog, 2024. [Online]. Available: https://www.anthropic.com/research/building-effective-agents

[12] Survey on Agent Workflow — Status and Future. arXiv:2508.01186. [Online]. Available: https://arxiv.org/pdf/2508.01186

[13] Agentic AI: Architectures, Taxonomies, and Evaluation of LLM Agents. arXiv:2601.12560. [Online]. Available: https://arxiv.org/html/2601.12560v1
