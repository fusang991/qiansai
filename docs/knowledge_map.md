# 知识地图（Knowledge Map）

> 用途：把散落在 journal 里的知识、命令、踩坑与决策收拢成一份**可复用导航**。
> 维护约定：新事实先记 journal，再回来在对应章节补一行并链证据；本文件不做历史替换。
> 初版：2026-09-23 16:18:35 Asia/Shanghai（[journal 记录](journal/20260923_161835_knowledge_map.md)）

## 0. 30 秒总览

- **项目**：AMD 3.1 竞赛 RTL 方向——ChipMATE-V-4B + ChipMATE-P-4B 双 4B 模型跑 VerilogEval v2（156 题），Icarus 独立评测。
- **已有硬结果**：基线 **109 PASS / 47 FAIL / 156**（69.87%，10825 秒 ≈3 小时，commit `0870769` 时代产出）；CPU 对照 151/5，其中 5 题为评测器局限（不改原分）。上游作者报告 pass@1/5 = 75.0/76.3（协议不同，仅参考）。
- **当前阶段**：Docker 里程碑（老师要求、无 sudo）。A100 试跑用 `vllm/vllm-openai:latest`（=0.30.0）做**管线试跑，结果不记成绩**；正式验收必须换回锁定的 **v0.19.1**。
- **正在等**：0.30.0 修复版全量试跑结果（2026-09-23 11:18 确认双服务 99% 满载在跑，`Result: PASS x/156` 与 `metrics.json` 待回报）。
- **竞赛要点**：**增益项 40 分 > 通过率项 30 分**（增益 = 同模型同推理服务的裸跑对照），详见 [competition.md](competition.md)。

## 1. 架构地图

### 1.1 目录职责

```
src/qiansai/           # 自研代码（唯一可改的业务代码区）
  runner.py            #   配置适配 + 原版工作流调用（JSONL 模式：--input/--out/--limit）
  case_runner.py       #   选题/落盘/汇总（--case 可重复 / --suite verilogeval-v2 /
                       #    --limit / --list-cases / --run-dir / --no-start / 超时两项）
  services.py          #   双服务编排：V→P 顺序启动(各 CUDA:0, 0.45)，就绪后透传执行
                       #   命令；退出码 0 全过/1 有失败/2 环境错误
  evaluation.py        #   Icarus 编译+仿真官方测试台的独立判定
  baseline.py          #   同模型裸跑入口（run_baseline.py）——增益项对照用
configs/
  serving.yaml         #   8001/8002、bfloat16、max_model_len 16384、max_num_seqs 3、
                       #   gpu_memory_utilization_per_service 0.45、
                       #   extra_args: --enforce-eager --language-model-only
  chipmate_4b.yaml     #   生成参数（轮数/采样，复现期不改）
model/weights/         #   两份权重(各 9078620536 B) + download_manifest.json（sha256 锁定）
data/
  verilog_eval/        #   子模块，dataset_spec-to-rtl：<task>.sv 题面、<task>_ref.sv 参考、
                       #   <task>_tb.sv 测试台 —— ref/tb 只许进评测侧
  processed/           #   verilogeval_v2.jsonl（跑题数据源）
runs/                  #   一切产物，只增不删；每次跑一个唯一目录
third_party/chipmate/  #   固定提交的上游子模块（复现期零改动）
docker/                #   Dockerfile.cuda / compose.cuda.yaml / entrypoint.sh / *.lock
scripts/               #   fetch_models.py、prepare_data.py、run_batch.sh、
                       #   run_docker.sh、setup_cuda.sh、serve_models.sh、smoke_test.sh
```

### 1.2 两条运行链路

**直跑链（老服务器 109/156 走的路）**

```
./run.sh --case/--suite
  → case_runner（选题, 建 runs/<stamp>_chipmate_<uuid8>/, 打印 Run directory:）
    → 服务未起则先调 services.py（V ready → P ready → Both ready）
      → ChipMATE 原版工作流 → 录制式生成器(POST 8001/8002, 双候选+反馈轮)
        → 最终候选 TopModule.sv → evaluation.py（iverilog 独立评测）
          → 每题实时落盘：generation.json / TopModule.sv / evaluation.json
  → 全部结束才写顶层 metrics.json + "Result: PASS x/156 | ..." → 退出码 0/1/2
```

**Docker 链（A100 现在走的路）**

```
.env (CUDA_VLLM_IMAGE/GPU_DEVICE_ID=0/MODEL_ROOT/DATA_ROOT/RUNS_ROOT, 相对 docker/ 解析)
  → bash scripts/run_docker.sh [--no-build] <run.sh args>
    （预检 docker/compose/.env/权重/数据 → compose build → run -T --rm qiansai ./run.sh）
      → 镜像内 entrypoint.sh：cd /app, 设 NO_PROXY, exec
        python -m qiansai.services --model-root /models -- "$@"
          → services.py 剥一个前导 "--" 后 subprocess.call(./run.sh …)   # 双"--"bug 已修
```

挂载：`src|configs|chipmate` 只读、`weights→/models` 只读、`data` 只读、`runs` 读写；
镜像名 `qiansai:cuda-local`；`shm_size 4gb`；端口 127.0.0.1:8001-8002；GPU `device_ids: ["0"]`。

### 1.3 双环境（严格分离）

| 环境 | 用途 | 关键内容 |
| --- | --- | --- |
| `.venv` | 工作流（CPU） | uv 管理、`uv.lock`、**Python 3.12**、pytest |
| `.venv-vllm` / 镜像内 `/app/.venv` | GPU 推理 | `docker/requirements.cuda.lock`（哈希锁定）：**vllm==0.19.1、transformers==5.5.3、nvidia-cutlass-dsl==4.4.2**，uv==0.9.18 |

## 2. 机器与网络档案

| 机器 | 身份/GPU | 网络 | 特记 |
| --- | --- | --- | --- |
| 本机（WSL） | 开发/文档 | — | **Docker CLI 存在但守护进程不可用**（"could not be found in this WSL 2 distro"），一切 docker 实测以 A100 为准并如实标注跳过 |
| 旧 AutoDL 服务器 | RTX 4080 SUPER，空闲 | GitHub/HF 通 | 连接参数在当轮对话中、**凭据永不入库**；109/156 基线产地；`uv` 不在非交互 PATH；连续关机 15 天释放数据 |
| **A100 服务器** | `j2-009@server3`，**A100 80GB PCIe**（driver 535.154.05 / CUDA 12.2），仓库嵌套在 `/home/j2-009/qiansai/qiansai` | **PyPI、Ubuntu apt、Docker Hub 通；GitHub、HuggingFace 封** | 无 sudo、在 docker 组；uv 已装 py3.14+py3.12；Docker 镜像加速器 `docker.registry.cyou` 曾拒绝连接（daemon 级、改不了 daemon.json）；首次推理已验证（39-token Verilog 补全，指纹 `vllm-0.30.0-a220ccc8`） |
| 32 GB 比赛容器 | 最终交付环境 | 官方平台 | 0.45×2 实测 29.49 GiB ✓；部署后必查 `nvidia-smi` ≈ 29-30/32 |

**网络对策速查**：HF 被封 → `HF_HUB_OFFLINE=1`（services.py 已设）+ 权重全本地；
GitHub 被封 → 不用 git pull 同步，走旧服务器中转 rsync；PyPI 通 → `QIANSAI_PYPI_INDEX` 可留默认。

## 3. 命令手册

### 3.1 工作流环境（任何机器）

```bash
rm -rf .venv                                   # 仅当被建成 3.14 时；重建必须 3.12
uv python install 3.12 && uv sync --frozen      # uv 先把 3.12 装上再 sync
.venv/bin/python -m pytest                     # 测试（bash 跑 .py 会 command not found）
bash scripts/smoke_test.sh                     # 脚手架改动后跑它
.venv/bin/python scripts/prepare_data.py       # 数据处理：永远用解释器跑 .py
```

### 3.2 直跑（非 Docker）

```bash
./run.sh --case Prob001_zero                          # 单题
./run.sh --case Prob007_wire --case Prob034_dff8      # 三题（部署检查题）
./run.sh --suite verilogeval-v2 --limit 3             # 全量抽 3
./run.sh --suite verilogeval-v2                       # 全量 156（≈3h, 放 tmux）
./run.sh --list-cases                                 # 列题号
bash run_baseline.py ...                              # 同模型裸跑（增益对照入口）
```

### 3.3 GPU 服务（非 Docker）

```bash
bash scripts/setup_cuda.sh                # 前置检查 iverilog/vvp/nvidia-smi → uv sync
bash scripts/serve_models.sh              # 起 V+P（前台），或后台按 journal 记法
curl --noproxy '*' http://127.0.0.1:8001/health
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
```

### 3.4 Docker（A100）

```bash
cd /home/j2-009/qiansai/qiansai
# .env 缺失脚本会自建；配镜像永远用 sed，不用 vi：
sed -i 's|^CUDA_VLLM_IMAGE=$|CUDA_VLLM_IMAGE=vllm/vllm-openai:latest|' .env
grep '^CUDA_VLLM_IMAGE=' .env                       # 必须回显有值

tmux new -s suite                                   # 3 小时任务先进 tmux
bash scripts/run_docker.sh --case Prob001_zero --case Prob007_wire --case Prob034_dff8
bash scripts/run_docker.sh --suite verilogeval-v2
bash scripts/run_docker.sh --no-build --suite verilogeval-v2   # 镜像没变时跳过构建
# 等价裸命令（怀疑脚本时用它二分定位）：
docker compose --env-file .env -f docker/compose.cuda.yaml build
docker compose --env-file .env -f docker/compose.cuda.yaml run -T --rm qiansai ./run.sh <args>
# 加速器抽风绕行（buildkit 元数据查询不回退官方源时）：
DOCKER_BUILDKIT=0 docker compose --env-file .env -f docker/compose.cuda.yaml build
```

退出码约定：**0 全过 / 1 有题失败（正常）/ 2 环境错误（找我）**。

### 3.5 结果观察（不打断运行）

```bash
RUN=$(ls -td runs/*_chipmate_* | head -1)   # 正在写的结果目录
ls -d "$RUN"/*/ | wc -l                     # 已完成题数 /156；watch -n 10 盯它
cat "$RUN/<题名>/evaluation.json"            # 单题判定；generation.json=生成；TopModule.sv=RTL
cat "$RUN/metrics.json"                     # 只在全部结束后存在
cat runs/*_services_*/logs/serve_v.log      # 服务启动日志
vim -R <文件>                               # 只读看产物；live 跟踪用 less +F
```

**文件创建规范**（本仓库惯例）：整文件用 heredoc（`cat > path <<'EOF'`），单行改动用
`sed -i`，多行结构化改动先 write/edit 本地再 heredoc 同步——**不依赖交互式编辑器**。

## 4. 踩坑全书（症状 → 根因 → 解法）

| # | 症状 | 根因 | 解法 / 现状 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | `bash scripts/prepare_data.py` → `command not found` | 用 bash 跑 Python 文件 | 一律 `.venv/bin/python <file.py>` | 早期 journal |
| 2 | `uv sync` 建出 3.14 的 .venv | 未指定解释器 | `rm -rf .venv` + `uv python install 3.12` 后重建 | 早期 journal |
| 3 | `setup_cuda.sh` 报 `Missing deployment prerequisite:` | 宿主机缺 iverilog/vvp/nvidia-smi | 转 Docker：镜像内 apt 装齐（Plan B: conda-forge `iverilog=11`） | server_setup.md |
| 4 | SSH `kex_exchange_identification` 连接被重置 | 网关限速（连打 3 次才通） | 等待重试；uv 在旧服务器非交互 PATH 上未证实，用回退路径 | 旧服务器审计 |
| 5 | `docker run ... nvidia-smi` 报模型名错误 | vllm 镜像 ENTRYPOINT 是 API server | `--entrypoint nvidia-smi` | A100 docker 探测 |
| 6 | curl `connection reset` | 服务未就绪 + 代理 | 等 `Application startup complete.` 再 `curl --noproxy '*'` | A100 docker 探测 |
| 7 | 测试里 `huggingface.co [Errno101] Network is unreachable` | HF 被封（预期内） | 权重全本地、离线环境变量；测试容器关掉 | A100 docker 探测 |
| 8 | `:latest` 实为 0.30.0 ≠ 锁定 0.19.1 | 镜像标签漂移 | **0.30.0 只做管线试跑，不记成绩**；正式换 `v0.19.1` | 版本核对 |
| 9 | build 报 `vllm-openai:lastest` | `.env` 手改拼写（latest→lastest） | `sed -i 's/lastest/latest/' .env` + grep 回显核对 | 本轮对话 |
| 10 | build `connect: connection refused`（`docker.registry.cyou`） | daemon 镜像加速器挂了；**dockerd 拉取会静默回退官方源，buildkit 元数据查询不会** | 重试 / `DOCKER_BUILDKIT=0` 绕行 / 根治=管理员改 daemon.json（无 sudo 只能请老师） | 本轮对话 |
| 11 | build `WARN: InvalidDefaultArgInFrom`（ARG 默认空） | lint 提示，compose 实际传入了 build-arg | 忽略（值非空就没事） | 本轮对话 |
| 12 | `Service error: [Errno 2] ... '--'` | run_docker.sh 多传一个 `--` + entrypoint 自带一个 + services.py 只剥一个 → 把 `--` 当程序名执行 | 删脚本末行 `qiansai` 后的 `--`（**已修**，本地+A100） | [journal 104931](journal/20260923_104931_run_docker_double_dash_fix.md) |
| 13 | vi 编辑 `.env` 反复失败 / `:wq` 回到原界面 | 交互编辑在远程会话里脆弱 | 仓库惯例：**单行 sed、整文件 heredoc**（§3.5） | 本轮对话 |
| 14 | 担心前台跑 3h 断线丢任务 | SSH 断 → 任务死 | `tmux new -s suite` / `tmux attach -t suite`；脚本已带 `-T` | 本轮对话 |
| 15 | nvidia-smi 占用 90%？ | `0.45×2=0.90` 预算**预分配**（设计如此，非泄漏），跑完释放 | 见 §7 显存账；顺带确认 A100=80GB | 用户截图 2026-09-23 |
| 16 | 本机无法验证 docker 运行 | WSL 无守护进程 | 所有 docker 实测由 A100 承担，报告中如实写"跳过" | 本轮对话 |

## 5. 红线与决策

### 5.1 硬红线（违反=数字作废）

1. **`*_ref.sv`、官方测试台只许进评测侧**；生成输入 = 题面 + 接口 stub（+ 未来获批的自写注释）。参考答案喂生成 = 自测自评，109/156 与一切增益全部失效（技能包含提示词会提交审查，一翻就见光）。
2. **基线 109/156 冻结**：新方法=新配置/新 runs 目录/新 journal，数字**不可与基线混比**；0.30.0 试跑结果同样不入账。
3. 上游复现期 ChipMATE 子模块与生成工作流**零改动**；子模块 gitlink 不顺手更新。
4. `runs/` 只增不删；**凭据/令牌/私钥永不写入仓库任何文件**（对话里出现过的旧服务器密码已提醒轮换）。
5. 提交/推送只按用户当轮授权；不 force push；提交前过 staging 与子模块修订。

### 5.2 已定决策（理由 + 证据）

| 决策 | 理由 | 证据 |
| --- | --- | --- |
| 锁 **vllm 0.19.1** | 支持 `Qwen3_5ForConditionalGeneration` 架构；109/156 与冒烟均产自此栈，锁定保可比 | [journal 20260911_120416](journal/20260911_120416_cloud_deployment.md)、server_setup.md |
| 双 venv 分离 | 工作流与 GPU 依赖互不污染 | decisions.md |
| `0.45` 不改 | 与 32G 基线同值保可比；`max_num_seqs:3` 已限并发，KV 富余；0.9 总额留 10% 安全 | decisions.md + 本轮 nvidia-smi |
| Docker 基底 = 钉版 vLLM 官方镜像 | 无 sudo；镜像自带整套 CUDA 栈，宿主机零依赖 | guides/server_setup.md |
| 0.30.0 = 管线试跑 | 版本漂移，防结果污染 | 版本核对 |
| 长任务一律 tmux | nohup/前台不防断线 | architecture.md |
| 错题本走**方案 A（离线建本、开跑前冻结）** | 规则把"跨题缓存/在线记忆/经验更新"列为**待赛事方确认**；冻结版=技能包，对齐 40 分增益项 | §6、competition.md |

### 5.3 竞赛评分与待确认问题

- 权重：**增益 40**（同模型同服务裸跑对照）> 通过率 30；Vivado 编译/仿真/综合三级；私有题集。
- 待问组委会（原文见 [competition.md](competition.md) §待确认）：双模型基线怎么定义、**裸跑时 P 服务是否保留加载**、评测期跨题记忆/经验更新的边界、第三方工具/Vivado 打包权限、预算与采样规则、提交包冻结与评测窗口。
- 五题评测器局限（Prob082/141/99/151/156）诊断归诊断，**原分不动**，修正须另发版本。

## 6. 错题本（技能包）方案草案 —— 待开工

> 方向：用户提出"错题的答案做错题本 + 简单相似度 + top-k 注释注入"，已确认合规边界
> （ref/tb 禁入；素材=自己的错代码+自己的失败归因），**方案 A 冻结注入**，等 0.30.0
> 试跑的 FAIL 作为第一批素材。

```
scripts/build_notebook.py
  扫 runs/ 历史 → data/processed/mistake_notebook.jsonl
  字段：task_id / failure_class（来自 evaluation.json 分类）/ note（泛化教训）/
        wrong_rtl（链接不复制）/ source_run
检索：TF-IDF 或 BM25（纯 Python、CPU、零显存、离线——HF 被封也无所谓）对题面算 top-k
注入：src/qiansai 生成包装层开关（配置项，默认关），top-k 注释 ≤200 token 拼入 prompt
      ——不改 chipmate 子模块、不碰基线路径
实验：三臂 ①同模型裸跑(baseline.py) ②现流程(109/156) ③流程+错题本
      增益=③−①（对齐 40 分口径），错题本贡献=③−②（消融）
```

显存：BM25 方案 **0 占用**；若日后上 embedding，A100 余量 ~8GB 或 32G 卡降到
`0.40×2` 腾 4GB 都塞得下。红线提醒：注释只写泛化教训，**不得可反推参考答案**；
在线边跑边记（方案 B）**先问组委会**再做。

## 7. 显存账速查

| 成分 | 32G 卡 | A100 80G | 说明 |
| --- | --- | --- | --- |
| 权重 ×2 | ≈18 GB（各 9.08 GB，manifest 锁定） | ≈18 GB | **两卡完全相同** |
| KV+工作区 ×2 | ≈11 GB（0.45×32−9.1/台） | ≈56 GB（0.45×80−9.1/台） | **按比例预分配，卡大就多占** |
| 合计 | ≈29.5 GB ✓ 合规 | ≈74 GB（73956/81920，99% util 正常满载） | 跑完全释放 |

结论：真实需求 ≈ 18G 权重 + 每台几 G KV；29G 是够用紧平衡（基线实证），74G 是同一比例
在大卡上的投影，**两者不矛盾**；比赛 32G 约束在比赛容器那张卡上自动收敛到 ~29G。

## 8. 待办清单

- [ ] **回报 0.30.0 全量试跑结果**：`Result: PASS x/156 | ...` 行 + `metrics.json` → 补 journal
- [ ] 正式验收：`.env` 改 `vllm/vllm-openai:v0.19.1`（先 `docker pull`、考虑 `@sha256` 钉 digest）→ rebuild → 三题 → 全量 156；途中如遇 `--language-model-only` 不识别、镜像内无 pytest、apt/uv 需镜像源 build-arg，按 §4 方式处置并记录
- [ ] 错题本方案 A：`build_notebook.py` + 注入开关 + 三臂实验（§6）
- [ ] 向组委会提问清单（§5.3），答复存原始记录与日期
- [ ] 32G 比赛容器部署时：查 `nvidia-smi` ≈29-30/32 并记 journal
- [x] 文档批次已随 `25ee3b2` 提交并推送（2026-09-23，含 4 个修改文档、`run_docker.sh`、
  10 篇 journal、本地图与并行会话的 AMD 迁移咨询）
- [ ] 后续里程碑：Vivado 分级评测、AMD/ROCm 部署（Dockerfile.rocm 同模式）、私有题泛化

## 9. 证据索引

- **基线**：[journal 20260911_193029_full_suite_results.md](journal/20260911_193029_full_suite_results.md)、`runs/20260911_140717_full_suite_session/assessment.json`（runs 不入 Git，按 journal 轻量结论）
- **规则**：[competition.md](competition.md)、[journal 20260911_222729](journal/20260911_222729_competition_review.md)、指南 PDF sha256 `5d2ac935...7a5a24`
- **环境与版本**：[journal 20260911_120416_cloud_deployment.md](journal/20260911_120416_cloud_deployment.md)、`docker/requirements.cuda.lock`
- **权重身份**：`model/manifest.json`（v `1e829e64...58826`、p `8ac6cacb...fb4d`）
- **A100 链路**：[journal 20260922_210341_a100_docker_probe.md](journal/20260922_210341_a100_docker_probe.md)、[journal 20260922_212639_a100_first_inference.md](journal/20260922_212639_a100_first_inference.md)（首次推理 39-token，`vllm-0.30.0-a220ccc8`）
- **Docker 脚本**：[journal 20260922_213542_run_docker_script.md](journal/20260922_213542_run_docker_script.md)、[journal 20260923_104931_run_docker_double_dash_fix.md](journal/20260923_104931_run_docker_double_dash_fix.md)
- **迁移与审计**：[journal 20260922_105847_restricted_network_a100_plan.md](journal/20260922_105847_restricted_network_a100_plan.md)、[journal 20260922_113600_autodl_disk_audit.md](journal/20260922_113600_autodl_disk_audit.md)
- **关键提交**：基线运行 `0870769`；本文件初版随 `25ee3b2` 提交推送（起点 `70f83c0`）
