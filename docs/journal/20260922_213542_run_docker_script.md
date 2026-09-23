# 2026-09-22 21:35:42 + Add run_docker.sh wrapper

- 时区：Asia/Shanghai
- 类型：本次工作；新增 Docker 运行包装脚本与文档同步
- 起始版本：70f83c085a81fe4a81d9e13853ca9776e4df9ce0
- 上一份相关记录：[20260922_212639_a100_first_inference.md](20260922_212639_a100_first_inference.md)

## 用户原始输入

> 不能把你上面的这些作为一个脚本放到scripts 文件夹里吗

指前文给出的三条命令：compose 三件套（`.env` 配置、
`docker compose build`、`run --rm qiansai -- ./run.sh` 三题验收）。

## 助手回复与实现

新增 scripts/run_docker.sh，固化该流程：

- `set -euo pipefail`，自解析仓库根目录，退出码遵循 run.sh 约定
  （0 全过、1 测试失败、2 环境错误），`exec` 透传容器退出码；
- 检测 docker 与 compose（优先 `docker compose` v2 插件，回退
  `docker-compose`）；
- `.env` 缺失时从 .env.example 创建并提示设置 CUDA_VLLM_IMAGE 后退出；
  CUDA_VLLM_IMAGE 为空报错；使用 `:latest` 时打印"结果与锁定基线不可比"
  警告；
- 构建前预检权重（两份 config.json 与 download_manifest.json）与
  data/processed，避免长构建后才失败；
- 支持 `--no-build` 跳过重复构建；`run -T` 支持 tmux/nohup；参数原样
  透传给容器内 ./run.sh。

## 验证

本机（WSL，Docker 守护进程不可用）已验证：

- `bash -n` 语法检查通过；
- 无参数 → 用法说明、退出码 2；
- PATH 剥离 docker → "docker is required."、退出码 2；
- docker CLI 在但无可用 compose/守护进程 → 从 .env.example 创建 .env、
  提示后退出码 2（测试后已删除生成的 .env）。

**跳过的检查**：`compose build` 与 `compose run` 的真实执行无法在本机验证
（Docker 守护进程不可用），将在 A100 的 0.30.0 试跑与 0.19.1 正式验收中
实测；未运行 pytest（本次为 shell 脚本，无 Python 行为变化）。

## 文档与发布

- 同步 docs/architecture.md 脚本清单、README.md Docker 入口、
  docker/README.md 容器契约第 7 条；
- 新增本 journal；未提交 Git，待用户确认后发布。
