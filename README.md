# qiansai

全国大学生嵌入式芯片与系统设计竞赛 2026，AMD 3.1 的 RTL 方向。
以 ChipMATE-V-4B 与 ChipMATE-P-4B 为首个模型方案，先在 NVIDIA 上复现，
再迁移到 AMD。采用独立比赛工程，固定版本保留上游代码。

**当前状态：本地架构与开发骨架。双模型推理、Docker 镜像构建和 AMD 运行尚未实测。**
用户将在后续提供 32 GB NVIDIA 云服务器。本阶段不安装 Vivado，也不下载大型模型权重。

## 文档入口

- [上下文与术语](docs/context.md)
- [当前共识与阶段目标](docs/decisions.md)
- [完整架构](docs/architecture.md)
- [逐次工作日志](docs/journal/)
- [协作规则](AGENTS.md)
- [原始赛题指南](docs/references/amd_2026_guide.pdf)

## 获取仓库

```bash
git clone --recurse-submodules https://github.com/fusang991/qiansai.git
cd qiansai
# 已经 clone 的仓库：
git submodule update --init --recursive
```

上游固定版本：

| 内容 | 来源 | 提交 |
| --- | --- | --- |
| ChipMATE | https://github.com/zhongkaiyu/ChipMATE | d94087b5159aea482648b26398a2ffb164246671 |
| VerilogEval v2 | https://github.com/NVlabs/verilog-eval | c498220d0a52248f8e3fdffe279075215bde2da6 |

官方 dataset_spec-to-rtl 包含 156 道题，每题有题目、参考实现和测试台。
上游各自的许可保留在子模块中；本仓库尚未另行选择自有代码的开源许可证。

## 本地准备与检查

Python 3.11 或更高版本可执行数据准备和骨架检查；推荐部署阶段使用 Python 3.12。
uv.lock 固定的是本工程的轻量 Python 依赖。GPU 推理栈由独立的镜像版本固定。

```bash
uv sync --frozen
python3 scripts/prepare_data.py
bash scripts/smoke_test.sh
```

数据转换结果在 data/processed/，只向生成流程提供题目和接口声明。
参考实现正文和官方测试台保留在 data/verilog_eval/，用于独立评测。

## 后续 NVIDIA 部署入口

Docker 文件是待实机验证的部署模板。先选择支持两份权重的 vLLM CUDA 镜像，
固定到标签或 digest，取得 Hugging Face 权重访问权限，并更新 model/manifest.json
中的具体 revision。部署机器需要能同时容纳两个模型及其运行缓存。

```bash
cp .env.example .env
# 编辑 .env：CUDA_VLLM_IMAGE、GPU_DEVICE_ID、MODEL_ROOT 等。
# 为 manifest 中两份模型填写固定 revision 后：
uv run python scripts/fetch_models.py
docker compose --env-file .env -f docker/compose.cuda.yaml build
docker compose --env-file .env -f docker/compose.cuda.yaml up -d
```

容器内有两个本地 vLLM 服务和 ChipMATE/Icarus 工作流；模型、数据和结果通过挂载持久保存。
首个云端验收目标是双模型加载、单题生成、自验证、原始输出落盘。

已经启动服务时，也可以在宿主机直接运行：

```bash
bash run.sh --input data/processed/verilogeval_v2.jsonl --out runs/manual/agent.jsonl --limit 1
bash run_baseline.sh --input data/processed/verilogeval_v2.jsonl --out runs/manual/baseline.jsonl --limit 1
```

单题开发入口目前接受只含一行的 JSONL；这不是尚未公布的官方提交协议。
批量封装见 scripts/run_batch.sh。正式独立评分与 Vivado 接口在后续阶段实现。

## 记录与存储

docs/journal/ 每次新增一份记录，三份核心文档维护当前共识。每次运行使用独立 runs/
目录，保留原始输入输出、配置、版本和日志。权重、大型运行产物、缓存和本机 .env
不进入普通 Git；其身份与需要分享的结果进入模型清单和工作日志。
被 Git 忽略不等于已经备份，迁移实验历史时还需同步相应 runs/ 和权重存储。
