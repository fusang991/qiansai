# 2026-09-11 11:12:34 + architecture_history

- 时区：Asia/Shanghai。
- 类型：历史补录，覆盖建仓前的架构讨论。
- 时间说明：文件时间为本次建仓首次记录到的时间，不伪造此前各轮的具体时分秒。
- 本条保存可见用户原文和助手最终答复。历史工具的关键发现另列；此前没有完整终端审计文件，
  因此不声称已恢复每次工具调用的全部原始输出。
- 原答复中的目录是当时提案，最新结构以 ../architecture.md 为准。

## 第一轮：任务背景

用户原文：

> 我们现在需要先确定仓库地架构。就是我告诉你我们要干什么的，我们需要完成嵌赛amd 地3.1 题，然后基本想法是先在 nvidia 上完成，然后迁移到amd 上。 你有什么问题吗？

助手最终答复：

有。我读了目录里的赛题指南。**先在 NVIDIA 上开发，再迁移到 AMD 是可行的**，指南明确开发阶段不限平台。不过，架构从一开始就要考虑最终的**单卡 32 GB、断网运行和容器交付**。

确定架构前，我主要有四个问题：

1. **你们准备主攻哪个 Track？**
   3.1 下有 RTL（Verilog/SystemVerilog）和 HLS（Vitis HLS C++），独立排名。这会直接影响工具接口、评测流程和技能包内容。
2. **目前可用的开发资源是什么？**
   NVIDIA 显卡的型号、显存和数量，以及 Vivado/Vitis 2025.2 的安装情况。推理和 EDA 工具是否需要放在不同机器上，也会影响架构。
3. **模型这部分，你们有什么既定想法？**
   是否已有候选模型、是否计划微调，以及希望把主要精力投入哪些方向。我倾向于先跑通“现成模型 → 生成 → 工具验证 → 反馈修复”的闭环，再用实验决定后续投入。
4. **除了这份指南，还有哪些官方材料？**
   特别是评分细则、基础镜像、单题输入输出协议和时间预算。指南里这些尚未完全确定，会影响提交入口与评测设计。

目前我的架构倾向是：**一个仓库，清楚分开智能体、技能包、推理服务、EDA 工具适配和评测记录**。NVIDIA/AMD 的差异主要收在推理服务和部署配置里；同时从第一版保留同模型的裸跑基线入口，方便持续衡量智能体究竟带来了多少提升。

## 第二轮：选定双 4B

用户原文：

> https://github.com/zhongkaiyu/ChipMATE 我就打算直接使用他们的双4b 方案，你觉得怎么样

助手最终答复：

我赞成，**可以把 ChipMATE 双 4B 定为第一版基座，仓库按 RTL 方向组织。** 它提供的模型和交叉验证流程，正好能作为我们后续优化的起点。

它的分工是：

- **V-4B**：生成 Verilog。
- **P-4B**：生成 Python 参考模型。
- 两者接受相同激励，比对输出，再根据不一致的地方修正代码。这两份权重已经做过专项训练。[模型说明](https://huggingface.co/core12345/ChipMATE-V-4B)

作者报告双 4B 在 VerilogEval V2 上达到 **75.0% / 76.3% 的 pass@1 / pass@5**，并称可以放进单张 24 GB 显卡。因此，值得优先尝试用它满足比赛的 32 GB 限制；实际显存还要连同缓存、上下文和并发一起测。[项目 README](https://github.com/zhongkaiyu/ChipMATE#benchmark-results)

我看过代码后，认为需要补上四块：

1. **接入比赛的 Vivado 验证流程。**
   上游交叉验证调用 `iverilog/vvp`；我们需要接入 Vivado 2025.2 的编译、仿真和综合反馈。两个模型输出一致，也可能共同误解题意，仍需独立评测。[验证代码](https://github.com/zhongkaiyu/ChipMATE/blob/d94087b5159aea482648b26398a2ffb164246671/chipmate/cross_verify.py)
2. **修正验证器中的具体问题。**
   我做了小型检查：端口解析会误读 `input signed`、漏掉合并声明的端口；模拟双方都缺失某个输出时，比较逻辑还会给出 `match_rate=1.0`。这些应该在接入时修掉，避免智能体被错误反馈带偏。[对应代码](https://github.com/zhongkaiyu/ChipMATE/blob/d94087b5159aea482648b26398a2ffb164246671/chipmate/cross_verify.py#L286)
3. **建立自己的基线和计时。**
   README 的配置每轮生成 3 对候选，最多 3 轮，一次工作流最多包含 **18 次模型生成**。其 pass@1 指一次完整工作流的结果。我们应保留 V-4B 同权重的单次裸跑入口，并分别测通过率、调用量和墙钟时间；双模型的正式基线口径再对照后续评分细则。[实验配置](https://github.com/zhongkaiyu/ChipMATE#paper-protocol-table-1)
4. **把推理服务独立出来，尽早验证 AMD。**
   上游已经通过两个本地服务调用模型，这个边界可以保留。vLLM 有 ROCm 支持，但这不等于这对权重在比赛显卡上的具体配置已经验证过。[vLLM 硬件支持](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/)

因此，我建议仓库保留**固定版本的 ChipMATE 上游代码**，我们自己的代码负责**比赛入口、验证器改进、Vivado 适配、技能包和评测**，CUDA/ROCm 配置放到独立的部署目录。第一阶段先比较“V-4B 裸跑、原版双模型、加入我们改进后的双模型”三组结果，再决定后续投入。

另外，两份权重目前都有 Hugging Face 访问条件，需要提前取得下载权限。你现在可用的 NVIDIA 显卡型号和显存是多少？

## 第三轮：文档与工程要求

用户原文：

> 你说的都是对的. 然后我们现在要确立文件夹，我认为有这么几点： 1. 自进化文档， 一个文档记录每次所有的信息， 可以就按照时间+关键词记录，目的是全保留。 核心共识文档，按照类别确定大概2-3个，比如 context.md就来确定我们当下的一些简称或者一些常用的名词，等等。 2. 其余文件夹的确定也符合工程规范，尽可能清晰 3. 我们第一步就是按照 他的方案部署.  vivado 之后再说，然后我们做rtl，对应的数据集你直接拉下来，然后整个系统用git管理

助手进度回复：

我会先把仓库结构和文档规则落下来：一份按时间追加的完整工作记录，以及三份按主题维护的共识文档。第一阶段按 ChipMATE 双 4B 部署 RTL 流程，拉取对应数据集并纳入 Git 管理；同时检查当前机器能承担哪些部署步骤。

用户中途补充：

> 你先给我三份你认为可行的架构

助手进度回复：

好，先比较三种架构，选定后再建目录和拉数据。目前我只做了环境检查，还没有修改仓库文件。

助手最终答复：

**我推荐第二种：独立比赛工程，固定版本保留 ChipMATE。** 它方便先复现原方案，也方便之后加入我们的改进。

三种方案当前都只围绕 **RTL、双 4B、Icarus Verilog、VerilogEval v2** 展开，Vivado 留到后续阶段。

三种方案共用同一套文档机制：

| 文件 | 职责 | 更新方式 |
| --- | --- | --- |
| `docs/journal.md` | 自进化日志：原始交流、操作、结果、失败、决策依据、待办 | 按“时间＋关键词”追加，保留历史 |
| `docs/context.md` | 常用名词、简称、项目背景、机器与资源信息 | 维护当前准确版本 |
| `docs/decisions.md` | 已达成的共识、当前阶段目标、范围与优先级 | 共识变化时更新，并关联日志 |
| `docs/architecture.md` | 目录职责、模块边界、数据流、运行方式 | 随工程结构更新 |

`journal.md` 保留原始信息，不能用一段摘要覆盖旧记录。长日志、生成代码等保存在对应运行目录中，由日志链接过去。三个共识文档负责让下一次工作快速进入状态。

**方案一：直接在 ChipMATE 仓库上扩展**

```text
qiansai/
├── chipmate/               # 上游源码，直接在这里修改
├── examples/               # 上游示例
├── paper_repro/            # 上游复现实验
├── docs/                   # 工作日志和共识文档
├── data/
│   └── verilog_eval/       # 官方数据集及评测脚本
├── model/                  # 模型声明和本地权重目录
├── serve/                  # 推理服务启动配置
├── configs/                # 实验参数
├── scripts/                # 下载、运行、评测脚本
├── skill/                  # 后续积累的领域经验
├── tests/
├── runs/                   # 按时间保存运行产物
├── AGENTS.md               # 仓库协作与文档维护规则
├── pyproject.toml
└── README.md
```

优点是部署路径最短，直接沿用上游工程。代价是后续修改会与上游代码混在一起，比较“原版”和“我们的版本”需要依赖 Git 分支或提交。

适合把项目长期作为 **ChipMATE 的一个分支**来维护。

**方案二：独立比赛工程，保留上游依赖——推荐**

```text
qiansai/
├── docs/
├── third_party/
│   └── chipmate/           # 固定版本的上游源码
├── src/
│   └── qiansai/            # 我们的入口、数据适配与评测代码
├── data/
│   └── verilog_eval/       # 固定版本的官方数据与评测器
├── configs/                # 双 4B、采样与运行参数
├── model/                  # 模型声明、版本及权重位置
├── serve/                  # NVIDIA / AMD 推理服务配置
├── scripts/                # 环境准备、下载与运行脚本
├── skill/                  # 我们积累的技能包
├── tests/
├── runs/                   # 每次运行的配置、输出和日志
├── AGENTS.md
├── pyproject.toml
└── README.md
```

第一阶段，`src/qiansai/` 只承担必要的输入输出适配，调用上游流程。后续再加入预算管理、验证器改进和 Vivado 接口。

优点是**上游复现与我们的改动边界清楚**，推理服务也能独立迁移。需要修改 ChipMATE 内部时，通过可追踪的补丁或受控 fork 管理，不让上游目录出现来源不明的改动。

适合我们现在的路线：**先部署，再测量，再逐步改进。**

**方案三：以实验研究为中心组织**

```text
qiansai/
├── docs/
├── third_party/
│   └── chipmate/
├── src/
│   └── qiansai/            # 各实验共享的运行与评测能力
├── methods/
│   ├── direct/             # 同模型直接生成
│   └── chipmate/           # 原版双模型方案
├── experiments/
│   └── reproduce_4b/       # 实验配置、说明及结果索引
├── data/
│   └── verilog_eval/
├── model/
├── serve/
├── scripts/
├── skill/
├── tests/
├── runs/
├── AGENTS.md
├── pyproject.toml
└── README.md
```

每种方法有独立入口，每个实验固定方法、模型、参数和数据版本。之后增加新的修复策略或消融实验，可以直接增加方法配置或实验目录。

优点是对比实验和报告整理最方便；代价是初期要多维护“方法”和“实验”两层组织。

适合后续会进行**大量策略比较、消融实验，甚至论文研究**的情况。

Git 管理上，三种方案都应做到：

- 自有代码、文档、配置、脚本和轻量实验结果进入 Git。
- ChipMATE、VerilogEval 固定到明确提交，可用 submodule 管理。
- 权重和大型运行产物单独保存，记录来源、版本、校验和与存储位置。
- 每次运行使用独立目录，保存当次配置和代码版本，避免覆盖历史结果。

**选择第二种即可满足当前需求；后续实验增多时，再自然增加第三种中的 `methods/` 和 `experiments/`。**

## 第四轮：日志按文件分开与 Docker

用户原文：

> 关于自进化文档，就是核心文档2-3份放在docs下。 然后docs下的journal 文件夹下放每次记录的日志。还有一个问题，就是为了方便迁移，是不是一开始就需要整个文件夹docker 化

助手最终答复：

**是的，建议从第一次部署就把完整运行流程容器化，同时用 Git 固定源码、配置和文档。** 这样迁移时可以重建明确的环境。

文档按你说的结构确定：

```text
docs/
├── context.md              # 名词、简称、项目背景、资源信息
├── decisions.md            # 当前共识、阶段目标、优先级
├── architecture.md         # 目录职责、模块边界、运行方式
└── journal/
    ├── YYYYMMDD_HHMMSS_architecture.md
    ├── YYYYMMDD_HHMMSS_chipmate_deployment.md
    └── ...
```

每次工作新增一份日志，保留原始交流、操作、结果、失败和待办；后续纠正在新记录中说明。三个核心文档持续更新，并链接到相关日志，方便追溯依据。

Docker 方面，我建议**第一阶段采用一个运行容器，内部启动两个模型服务，再运行 ChipMATE 和 Icarus**。代码中继续保留独立的推理接口，之后也能连接远程模型服务。这也比较容易衔接比赛最终要求的单容器交付。

部署文件可以集中在：

```text
docker/
├── Dockerfile.cuda         # 首阶段 NVIDIA 环境
├── Dockerfile.rocm         # AMD 迁移阶段补齐
├── entrypoint.sh           # 启动服务、等待就绪、处理退出
├── compose.cuda.yaml       # NVIDIA 设备与目录挂载配置
└── compose.rocm.yaml       # AMD 迁移阶段补齐
```

有三个边界需要从一开始明确：

- **两套 GPU 环境，共用业务代码。** NVIDIA 使用 CUDA 镜像，AMD 使用 ROCm 镜像，分别固定经过验证的版本。vLLM 官方也分别提供这两类镜像。[vLLM 容器文档](https://docs.vllm.ai/en/latest/deployment/docker/)
- **文件持久保存在仓库或宿主机。** 开发时挂载源码；权重、数据集和 `runs/` 挂载到固定路径。这样修改代码方便，删除容器也不会丢失实验记录。发布时再把确定版本的代码和离线依赖装入镜像。
- **宿主机负责 GPU 驱动与设备访问。** Docker 固定用户态依赖，迁移后仍需检查驱动兼容性、显存和运行结果。[AMD 容器说明](https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.2/how-to/docker.html)

另外，启动和评测脚本应当也能直接运行，Docker 复用这些脚本。这样遇到已经运行在容器中的云机器，也能使用同一套入口。

## 第五轮：选择方案二与最终目录

用户原文：

> 我觉得就用方案2吧，最后的架构是怎么样的

助手最终答复：

最终采用**方案二：独立比赛工程＋固定版本的 ChipMATE**，加上你确定的文档结构和从第一阶段开始的 Docker 部署。

建议最终目录如下，标注“后续”的部分届时再添加：

```text
qiansai/
├── README.md                       # 项目入口、环境要求、部署与运行步骤
├── AGENTS.md                       # 协作规则、文档维护要求、工作流程
│
├── docs/
│   ├── context.md                  # 名词、简称、背景、机器与资源信息
│   ├── decisions.md                # 当前共识、阶段目标、范围与优先级
│   ├── architecture.md             # 目录职责、模块边界、数据流
│   ├── journal/
│   │   ├── _template.md            # 每次工作记录的统一模板
│   │   └── YYYYMMDD_HHMMSS_keyword.md
│   └── references/
│       └── amd_2026_guide.pdf       # 当前赛题说明，保留原始内容
│
├── third_party/
│   └── chipmate/                   # Git submodule，固定上游提交
│
├── src/
│   └── qiansai/
│       ├── __init__.py
│       ├── runner.py               # 调用 ChipMATE，管理输入输出
│       ├── baseline.py             # V-4B 同权重单次直接生成
│       ├── datasets.py             # 数据集格式适配
│       └── evaluation.py           # 独立评测、指标统计
│
├── configs/
│   ├── chipmate_4b.yaml             # 候选数、轮数、采样、验证参数
│   └── serving.yaml                # 模型路径、上下文、显存预算、服务地址
│
├── docker/
│   ├── Dockerfile.cuda             # NVIDIA 运行环境
│   ├── compose.cuda.yaml           # GPU、目录挂载与启动配置
│   ├── entrypoint.sh               # 启动两个模型服务、等待就绪、处理退出
│   ├── Dockerfile.rocm             # 后续：AMD 运行环境
│   └── compose.rocm.yaml           # 后续：AMD 设备与启动配置
│
├── model/
│   ├── MODEL.md                    # 模型来源、版本、精度与实测显存
│   ├── manifest.json               # 权重版本、文件清单与校验信息
│   └── weights/                    # 本地权重，不直接提交到 Git
│
├── data/
│   ├── verilog_eval/               # Git submodule，官方数据与评测脚本
│   └── processed/                  # 转换后的输入，由脚本生成
│
├── scripts/
│   ├── fetch_models.py             # 下载指定版本权重
│   ├── prepare_data.py             # 准备 VerilogEval v2 输入
│   ├── run_batch.sh                # 批量运行
│   └── smoke_test.sh               # 检查服务与最小任务闭环
│
├── tests/                          # 自有适配与评测逻辑的必要测试
├── skill/                          # 后续：沉淀经过验证的领域经验
│
├── runs/
│   └── YYYYMMDD_HHMMSS_keyword/
│       ├── manifest.json           # 代码、模型、数据、镜像版本及命令
│       ├── config.yaml             # 本次实际使用的配置快照
│       ├── inputs.jsonl            # 本次输入
│       ├── outputs.jsonl           # 模型与工作流输出
│       ├── metrics.json            # 通过率、耗时等指标
│       ├── logs/                   # 原始运行日志
│       └── tasks/                  # 各题生成代码与验证产物
│
├── run.sh                          # 单题运行入口
├── run_baseline.sh                 # 单题裸跑基线入口
├── pyproject.toml                  # 自有 Python 工程与依赖声明
├── uv.lock                         # Python 依赖锁定
├── .env.example                    # 本地路径、设备等配置示例
├── .gitmodules                     # 上游代码与数据集来源
├── .gitignore
└── .dockerignore
```

这套结构的职责划分是：

- **`docs/` 管知识和共识。** 三份核心文档维护当前状态；`journal/` 每次新增记录，保存原始交流、操作、结果、失败和决策依据，关联对应运行目录。
- **`third_party/` 保留可复现的上游版本。** 第一阶段直接复现其流程，我们的适配代码放在 `src/qiansai/`。
- **`configs/` 管运行参数，`docker/` 管运行环境。** 推理服务的启动也统一放在这里。
- **`data/` 管数据，`model/` 管权重，`runs/` 管实验产物。** 每次运行独立保存，配置和结果不会相互覆盖。
- **Git 管理源码、文档、脚本、配置及上游版本指针。** 权重和大型产物单独持久保存，仓库记录版本、校验信息与结果索引。

第一阶段的运行方式是：**一个 NVIDIA 容器内启动 V-4B、P-4B 两个推理服务，以及 ChipMATE＋Icarus 工作流**；源码、权重、数据和结果目录按需挂载。先完成原方案在 VerilogEval v2 上的部署与复现，再进入改进和 AMD 迁移阶段。

## 第六轮：迁移成本

用户原文：

> 到时候从nvidia 迁移到 amd 方便吗？

助手最终答复：

**按现在的架构，迁移工作能集中在推理环境和部署配置上，业务代码大部分可以复用。** 但还需要在 AMD 实机上验证，不能把 Docker 当成兼容性保证。

| 部分 | 迁移时的处理 |
| --- | --- |
| ChipMATE 控制流、提示词、数据处理、日志 | 基本直接复用 |
| V-4B、P-4B 权重 | 优先复用同一份权重 |
| Icarus 仿真与评测 | 基本直接复用 |
| 推理环境 | CUDA 版切换为 ROCm 版 |
| GPU 访问配置 | 使用 AMD 对应的设备配置 |
| 显存分配、并发、推理算子 | 在目标卡上重新验证和调整 |

vLLM 已分别提供 NVIDIA 和 ROCm 容器镜像，这为迁移提供了现成基础；宿主机仍需要兼容的驱动。[vLLM 容器文档](https://docs.vllm.ai/en/latest/deployment/docker/)、[AMD 容器说明](https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.2/how-to/docker.html)

**真正的不确定性是：ChipMATE 使用的 Qwen3.5 架构，在目标 Radeon 卡上的推理兼容性、速度，以及两个模型同时运行时的总显存。** 这些目前还没有实测。

为此，从第一天就固定三个边界：

- 业务代码只通过统一接口调用模型，GPU 依赖集中在推理环境。
- 模型、数据、镜像和配置都记录版本，方便定位迁移前后的差异。
- **NVIDIA 最小闭环跑通后，尽早做一次 AMD 双模型加载和少量题目验证。**

这样后续的主要工作就是切换环境、调整参数和回归验证，迁移成本会比较可控。

## 历史工具检查与结论

- 读取本地赛题 PDF，使用 pdftotext 提取 3.1 内容，核对赛道、环境、提交与基线要求。
- 检查当时目录：只有赛题 PDF，Git 尚未初始化。
- 在临时目录读取 ChipMATE 提交 d94087b5159aea482648b26398a2ffb164246671。
- 检查上游 inference.py、backends.py、cross_verify.py、README、paper_repro/。
- 最小解析检查：input signed 被误读为 signed 端口，合并声明中的第二个端口漏读。
- 模拟缺失输出检查：SV 输出缺失、Python 输出 None 时，自验证给出 match_rate=1.0。
- 这些是源码与 CPU 逻辑检查，不是模型部署或论文结果复现。
- 查阅 vLLM 与 AMD 官方容器文档，确定 GPU 依赖和宿主驱动的分工。
- 本机检查发现 RTX 4060 Laptop 8 GB、WSL2、Icarus 12.0。
- 当时 GitHub DNS 请求被沙箱阻断；用户要求先看方案，所以未在那个阶段继续拉取数据。
