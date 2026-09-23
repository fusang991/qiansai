# 本地文件、服务器文件与新服务器部署

本文记录 2026-09-11 已核对的部署方式，方便在新 NVIDIA 服务器上恢复工程。
现有能力是：**首次准备环境和权重，之后一条命令运行 testcase。**
仅执行 git clone 还不能直接开始模型推理。

## 本地、服务器和 Git 分别有什么

本地工程根目录为 /home/young/autodl/qiansai；
当前服务器工程根目录为 /root/autodl-tmp/qiansai。
下面的路径均相对于各自的工程根目录。

| 内容 | 本地电脑 | 当前服务器 | Git clone 能否恢复 |
| --- | --- | --- | --- |
| 自有代码、脚本、配置、文档 | 有 | 有 | 能 |
| third_party/chipmate：固定版本的上游代码 | 有 | 有 | 能，需拉取子模块 |
| data/verilog_eval：156 题原始数据、参考实现和测试台 | 有 | 有 | 能，需拉取子模块 |
| data/processed：转换后的题目 | 已生成 | 已生成 | 不直接保存，安装脚本会重新生成 |
| .venv：工作流 Python 环境 | 已安装 | 已安装 | 不保存已安装环境，按 uv.lock 重建 |
| .venv-vllm：GPU 推理环境 | 没有项目 GPU 环境 | 已安装 | 按 docker/requirements.cuda.lock 重建 |
| model/weights：两个 4B 模型的实际文件，合计约 18 GB | 没有，只有占位文件 | 有完整权重和下载清单 | 没有，Git 只保存模型身份和校验信息 |
| runs：完整实验产物 | 已备份全量实验及参考对照 | 有原始结果 | 不保存完整产物，文档中有结果说明 |

当前服务器的 .venv-vllm 是一个链接，实际目标是系统盘上的
/root/qiansai-envs/vllm-0.19.1。项目、权重和结果在数据盘。
只复制项目目录不会自动带走该链接指向的环境。

Git 保存的是工程和重建依据；模型文件、已安装环境和完整历史结果需要分别处理。
被 .gitignore 忽略不等于已经备份。

## 新 NVIDIA 服务器先准备什么

选择持久化目录存放工程，并确认：

- Git 可用，服务器能够访问本仓库及两个上游子模块；需要权限时先完成授权。
- NVIDIA 驱动可用，nvidia-smi 能识别 GPU，驱动兼容项目锁定的 CUDA 运行环境。
- Python 3.12、uv 0.9.18、Icarus Verilog（iverilog 和 vvp）及编译工具已安装。
- 磁盘能容纳两份模型、两个 Python 环境、下载缓存和后续实验产物。
- 若重新下载权重，Hugging Face 账号具有两份模型的访问权限。

[scripts/setup_cuda.sh](../../scripts/setup_cuda.sh) 不会安装宿主机驱动或代替以上基础准备。
当前 GPU 依赖锁对应 vLLM 0.19.1、PyTorch 2.10.0 / CUDA 12.8，
迁移时先保持版本一致，确认运行后再另行评估升级。

## 第一步：获取工程和数据集

在选好的持久化目录中执行：

```bash
git clone --recurse-submodules https://github.com/fusang991/qiansai.git
cd qiansai
```

--recurse-submodules 会获取固定版本的 ChipMATE 和 VerilogEval。
如果已经普通 clone，可以在工程根目录补执行：

```bash
git submodule update --init --recursive
```

不使用 --remote 更新子模块，以免改变已固定的复现版本。
如果目标服务器不能直接访问仓库，可以使用经授权的 Git bundle 传输代码；
bundle 不会自动带上未跟踪的权重、运行产物或两个子模块的完整内容。

## 第二步：安装运行环境

后续命令均在工程根目录执行：

```bash
bash scripts/setup_cuda.sh
```

脚本会创建工作流 .venv 和独立 GPU 环境 .venv-vllm，
按依赖锁安装、检查 GPU 环境包兼容性、生成 data/processed，
并通过 smoke 脚本调用 pytest。

这一步通过只说明依赖安装和 CPU 检查通过；两个模型的真实 GPU 运行还要在后面验证。
新机器通常按脚本重建环境，不直接复制旧机器的虚拟环境。
如果搬来的是旧工程目录，先检查 .venv-vllm 是否仍指向旧机器的绝对路径。

## 第三步：准备两份模型权重

以下两种方式选择一种。

### 方式 A：重新下载

```bash
.venv/bin/hf auth login
.venv/bin/python scripts/fetch_models.py
```

交互登录具有两份模型访问权限的账号。下载脚本按照
[model/manifest.json](../../model/manifest.json) 的固定 revision 下载，
并保存文件 SHA256 清单。凭据使用标准登录缓存，不写进文档或 Git。

### 方式 B：从旧服务器复制

把旧工程的整个 model/weights/ 复制到新工程的同名位置，再核对校验清单。
这种方式可跳过上面的登录和下载命令。

完整目录需要包含：

- chipmate-v-4b 的模型权重、配置和分词器文件。
- chipmate-p-4b 的模型权重、配置和分词器文件。
- 对应的 download_manifest.json 等下载校验信息。

不能只复制两个 model.safetensors 文件而漏掉其余模型文件。
本地电脑目前没有这两份实际权重，不能从本地工程直接获得模型文件。

## 第四步：验证三题，再运行全量

先运行旧服务器已经通过的三道部署检查题：

```bash
./run.sh --case Prob001_zero --case Prob007_wire --case Prob034_dff8
```

入口会检查并按需启动两个模型服务，运行 ChipMATE 生成和交叉验证，
再调用 Icarus 进行独立评测，最后显示结果和产物路径。

确认新机器的启动、显存和结果正常后，再运行全部 156 题：

```bash
./run.sh --suite verilogeval-v2
```

以后只运行一题时：

```bash
./run.sh --case Prob001_zero
```

每次实验保存在新的 runs/ 目录，包括最终 RTL、模型交互记录、评测日志和 metrics.json。
退出码 0 表示全部通过，1 表示有功能或编译失败，2 表示环境、生成或其他执行错误。
全量跑完不等于全部通过：旧服务器初版结果是 109 PASS / 47 FAIL，全部 156 题均已执行。

run.sh 本身是前台入口。长任务如需在断开 SSH 后继续，应通过 nohup 或 tmux 启动，
并保存日志和退出状态；这些方式不能让任务跨服务器关机继续执行。

## 旧实验结果是否必须迁移

**运行新的 testcase 不依赖旧 runs/。**

需要追溯旧实验时，再单独复制对应 runs/ 目录到新机器或长期产物存储。
目前本地已有全量实验、控制日志和参考实现对照副本。
复制历史时保留原目录和版本信息，不覆盖旧实验。

## 受限网络服务器：无 GitHub/HuggingFace 的直连迁移（计划，未实测）

目标 A100 能联网但访问不了 GitHub 和 HuggingFace 时，方案大幅简化：
PyPI（或国内镜像）可达，两个 Python 环境直接在 A100 上安装；
唯一必须从旧服务器带过去的是**代码（含子模块与 `.git`）和权重**。
`scripts/setup_cuda.sh` 第 6 行已支持 `QIANSAI_PYPI_INDEX` 换源，
`uv sync` 另需 `UV_DEFAULT_INDEX` 指向同一镜像。
`src/qiansai/services.py` 启动模型时设置 `HF_HUB_OFFLINE=1` 并从
`MODEL_ROOT` 本地目录 serve，运行期不访问 HuggingFace。

A100 上拉取（-P 支持断点续传）：

```bash
rsync -avP --exclude='.venv' --exclude='.venv-vllm' --exclude='runs' \
    root@旧服务器:/root/autodl-tmp/qiansai/ /opt/qiansai/
cd /opt/qiansai
export QIANSAI_PYPI_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
export UV_DEFAULT_INDEX="$QIANSAI_PYPI_INDEX"
bash scripts/setup_cuda.sh
```

setup_cuda.sh 会创建 .venv 与 .venv-vllm、按哈希锁安装 GPU 依赖、
生成 data/processed 并运行 pytest smoke。随后校验权重并验收
（跳过 fetch_models.py，权重已随 rsync 到位）：

```bash
sha256sum model/weights/chipmate-v-4b/model.safetensors \
          model/weights/chipmate-p-4b/model.safetensors
# 与 model/manifest.json 固定值核对后，进入"第四步：验证三题，再运行全量"
```

检查项：`uv --version` 应为 0.9.18（uv.lock 由该版本生成，版本差异过大
会报 lockfile 不兼容，可从旧服务器拷贝单文件 uv 二进制）；
`git`、`iverilog`、`vvp`、`nvidia-smi` 在位（Ubuntu 源可达可直接 apt 安装）；
磁盘建议 ≥ 80 GB。工程必须带 `.git`（含 `.git/modules`）整体传输，
数据集 revision 检查依赖 `git -C data/verilog_eval rev-parse HEAD`。

### 完全无网的备用方案：wheelhouse

若目标机连 PyPI 都不可达，才需要在旧服务器预下载离线 wheel 仓库
（wheelhouse，`pip download` 得到的 .whl 目录，安装时
`--no-index --find-links`）：`uv export --frozen --no-hashes` 导出
工作流 pin 后下载 wheelhouse-workflow；
`pip download --require-hashes -r docker/requirements.cuda.lock`
下载 wheelhouse-vllm；`uv build --wheel` 打包 qiansai 与 chipmate；
A100 上 `uv venv` + `uv pip install --no-index --find-links` 重建两个环境。
旧服务器的 .venv-vllm 是指向系统盘的符号链接，任何方案都必须排除。
以上为依据现有锁文件整理的计划，尚未在受限网络机器实测；
执行后按结果更新本节。

## A100 与 Docker 的当前边界

A100 仍属于 NVIDIA/CUDA 路线，预计复用上述入口；本项目尚未在 A100 实测。
新机器应重新确认两个服务的显存用量。当前配置为每服务 0.45 的显存比例，
更大显存的卡沿用该比例不代表仍满足比赛的 32 GB 限制。

当前服务器使用云平台已有容器和两个 Python 环境。
仓库自有 Dockerfile/Compose 尚未构建验收，不能把它们当成已经验证的一键迁移镜像。
AMD/ROCm 和 Vivado 不属于本操作步骤的已验证范围。

## 维护与依据

本文是操作手册。三份核心共识仍为 context.md、decisions.md 和 architecture.md。

- [仓库架构与部署边界](../architecture.md)
- [本地与服务器分工的核对记录](../journal/20260911_211722_architecture_review.md)
- [A100 迁移、关机与备份的核对记录](../journal/20260911_213632_a100_shutdown_review.md)
- [Git clone 恢复范围的核对记录](../journal/20260911_220716_clone_recovery.md)
- [本操作手册的创建记录](../journal/20260911_221518_server_setup_guide.md)
