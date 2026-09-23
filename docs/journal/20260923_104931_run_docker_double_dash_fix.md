# 2026-09-23 10:49:31 + run_docker.sh double-dash fix

- 时区：Asia/Shanghai
- 类型：本次工作；修复 run_docker.sh 传参 bug（首轮 A100 Docker 试跑排障）
- 起始版本：70f83c085a81fe4a81d9e13853ca9776e4df9ce0
- 上一份相关记录：[20260922_213542_run_docker_script.md](20260922_213542_run_docker_script.md)

## 用户原始输入（按时间）

1. （A100 执行 `bash scripts/run_docker.sh --suite verilogeval-v2`）贴出首个构建失败：
   `load metadata for docker.io/vllm/vllm-openai:lastest` →
   `Head "https://docker.registry.cyou/v2/..." ... connection refused`，问"为什么有报错了"、
   "还是同一份吗？"。
2. 贴出第二份日志（新执行）：构建成功 `naming to docker.io/library/qiansai:cuda-local`、
   `V model ready.`、`P model ready.`、`Both local model services are ready.`，随后
   `Service error: [Errno 2] No such file or directory: '--'`。
3. "对，第二份日志哪里弄错了。可能是我哪里拼写出错了吗？"

## 助手回复要点与处理

- 确认第一份仍是同一份旧输出（`lastest` 与耗时 61.3s/124.8s/186.5s 完全一致）。
- 旧构建失败含两个独立问题：① `.env` 中 `latest` 拼为 `lastest`（给出
  `sed -i 's/lastest/latest/' .env`）；② 守护进程配置的加速器
  `docker.registry.cyou`（128.242.245.221:443）拒绝连接——dockerd 拉取失败会
  静默回退官方源（故早先 `docker pull` 成功），buildkit 元数据查询不回退故撞死；
  给出备选 `DOCKER_BUILDKIT=0` 传统构建器与"请管理员修 daemon.json
  registry-mirrors"（用户无 sudo）。
- **第二份日志的失败不是用户拼写错误，是本轮新写的 run_docker.sh 的 bug。**

## 根因（本地 git 核实）

- `docker/entrypoint.sh` 固定执行
  `python -m qiansai.services --model-root /models -- "$@"`，自带一个 `--` 分隔符；
- run_docker.sh 原第 70 行 `compose run -T --rm qiansai -- ./run.sh "$@"` 又传了
  一个 `--`，compose 将其随命令透传进容器；
- services.py（22adce9 与 HEAD 一致，第 205 行）只剥离**一个**前导
  `--`（`args.command[1:] if args.command[:1] == ["--"]`），第 207 行
  `subprocess.call(command)` 把剩余的 `--` 当程序名执行 →
  `[Errno 2] No such file or directory: '--'`。
- 核实命令：`git show 22adce9:src/qiansai/services.py`（strip 在位）、
  `git show 22adce9:docker/entrypoint.sh`（`-- "$@"` 在位）、
  `git diff --stat 22adce9..HEAD -- src/ docker/ scripts/ run.sh` 输出为空
  → A100（rsync 自旧服务器）与本地 HEAD 源码完全一致，排除"旧代码"假设。
- 即 A100 现场 = HEAD 源码 + 本脚本的多余 `--`；Docker 模板此前从未实机验证
  （仓库既有注记），该组合缺陷首次实测暴露。

## 修改

- `scripts/run_docker.sh`：删除 compose run 命令中的多余 `--`，头部示例注释同步，
  并新增三行注释说明 entrypoint/services 的 `--` 剥离约定，防止回归。
- 本机验证：`bash -n` 通过；`grep` 确认第 4 行与第 72 行均无多余 `--`。
- **跳过的检查**：Docker 构建/运行本机不可验证（守护进程不可用），修复的实测
  由 A100 重跑承担；未运行 pytest（shell 单行改动）。

## 给 A100 的修复命令（用户侧待执行）

```bash
sed -i 's|qiansai -- ./run.sh|qiansai ./run.sh|' scripts/run_docker.sh
grep -n 'qiansai ./run.sh' scripts/run_docker.sh
tmux new -s suite
bash scripts/run_docker.sh --no-build --suite verilogeval-v2
```

镜像已建成（qiansai:cuda-local），`--no-build` 直接进服务启动（约 2–4 分钟），
预期过 `Both local model services are ready.` 后进入逐题输出。

## 未尽事项

- A100 执行上述修复并重跑全量（约 3 小时，tmux 内）；观察 `lastest`/加速器问题
  是否随 `sed` 一并消失。
- 全量通过后仍需：`.env` 切 `vllm/vllm-openai:v0.19.1` 正式验收、按实际 A100
  显存重算 `gpu_memory_utilization_per_service`。
- 本 journal、run_docker.sh 及此前 7 篇 journal、server_setup.md 修改均未提交。
