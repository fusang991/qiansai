# 2026-09-22 10:58:47 + Restricted-network A100 plan revision

- 时区：Asia/Shanghai
- 类型：本次工作；部署方案修订与概念说明，未执行任何实际传输或 A100 验收
- 起始版本：70f83c085a81fe4a81d9e13853ca9776e4df9ce0
- 上一份相关记录：[20260922_105403_offline_a100_rsync_plan.md](20260922_105403_offline_a100_rsync_plan.md)

## 用户原始输入

> wheelhouse 这是什么意思？ 我的新服务器可以用uv， 可以联网，只是连不了github 和huggingface

## 助手回复要点

### wheelhouse 的含义

wheelhouse（轮子仓库）是一个装满 `.whl` 文件的目录：在有网的机器上用
`pip download` 把依赖锁里所有包预先下载好，到无网机器上用
`pip install --no-index --find-links <目录>` 安装，全程不再联网。
它只服务于"彻底无网"的场景。

### 用户澄清后的方案简化

新 A100 能联网、只是 GitHub 与 HuggingFace 不可达，因此 PyPI（或国内
镜像）可达，wheelhouse 备用方案降级为不需要：torch、vLLM、transformers
等全部来自 PyPI。必须从旧服务器带过去的只剩两样：代码（含子模块与
`.git`）和 18 GB 权重。

代码层证据：

- scripts/setup_cuda.sh 第 6 行 `QIANSAI_PYPI_INDEX` 已支持换源，
  用于 `uv pip install --require-hashes -r docker/requirements.cuda.lock`；
  `uv sync --frozen` 另需 `UV_DEFAULT_INDEX` 指向同一镜像。
- src/qiansai/services.py 第 67–117 行：从 `MODEL_ROOT` 本地目录
  `vllm serve`，启动环境设置 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`
  并移除 HF 凭据，运行期不访问 HuggingFace；
  download_manifest.json 校验 repo_id/revision 与 model/manifest.json 一致。

修订后步骤（A100 上）：

1. `rsync -avP --exclude='.venv' --exclude='.venv-vllm' --exclude='runs'
   root@旧服务器:/root/autodl-tmp/qiansai/ /opt/qiansai/`
2. `export QIANSAI_PYPI_INDEX=<镜像>`、`export UV_DEFAULT_INDEX=<镜像>`，
   `bash scripts/setup_cuda.sh`（建两个环境、生成 data/processed、pytest smoke）
3. 跳过 fetch_models.py；`sha256sum` 校验两份 safetensors 与
   model/manifest.json 一致；pytest → 3 道部署检查题 → 全量 156 题。

检查项：uv 版本应为 0.9.18（uv.lock 由其生成，差异过大报 lockfile
不兼容，可拷旧服务器单文件二进制）；git/iverilog/vvp/nvidia-smi 在位；
磁盘 ≥ 80 GB；工程必须带 `.git`（含 `.git/modules`）整体传输。
GitHub/HF 不可达不影响任何步骤：原本需要它们的只有 clone 子模块和
下载权重，均由旧服务器携带完成。

## 文件、验证与发布

- 改写 docs/guides/server_setup.md：原"离线（无网）服务器"小节改为
  "受限网络服务器：无 GitHub/HuggingFace 的直连迁移"，wheelhouse 降级为
  完全无网时的备用小节，均标注未实测计划。
- 新增本 journal。未修改源码、依赖锁、模型清单、子模块与运行产物；
  未启动 pytest、GPU testcase、Docker、AMD 或 Vivado 验收。
- 本轮未执行 git commit/push，待用户确认后发布。
