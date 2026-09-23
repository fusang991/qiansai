# 2026-09-22 11:36:22 + AutoDL server disk audit

- 时区：Asia/Shanghai
- 类型：本次工作；旧服务器只读现场审计，为 A100 受限网络迁移做盘点
- 起始版本：70f83c085a81fe4a81d9e13853ca9776e4df9ce0
- 关联运行目录：[本次审计](../../runs/20260922_113600_autodl_disk_audit/)
- 上一份相关记录：[20260922_105847_restricted_network_a100_plan.md](20260922_105847_restricted_network_a100_plan.md)

## 用户原始输入

> ssh -p 48226 root@connect.weste.seetacloud.com
> （密码，按约定不写入文档）
>
> 这是我目前的账号和密码，给我能直接跑的命令

## 助手回复要点

按此前承诺直接连接旧服务器执行只读审计，未改动服务器任何文件。
原始输出与命令清单存于关联 runs/ 目录；凭据不写入任何仓库文件。

### 审计结果（2026-09-22 11:35 服务器时钟，更新 2026-09-11 的记录）

主机：autodl-container-denn6q3zb9-a9f6124e，Ubuntu 22.04.5 LTS，
up 88 days；GPU RTX 4080 SUPER 显存占用 1 MiB，无 vllm/qiansai 进程，
实例空闲可随时做传输。load average 24–39 为共享宿主机内核读数，
容器自身无计算进程，不代表本实例负载。

数据盘 /root/autodl-tmp（50 GB，用 39 GB，余 12 GB）：

| 内容 | 大小 | 说明 |
| --- | --- | --- |
| qiansai/model/ | 17 GB | 两份权重 chipmate-v-4b、chipmate-p-4b 各 8.5 GB + download_manifest.json |
| qiansai/runs/ | 2.7 GB | 全部实验产物（2026-09-11 指纹只覆盖其中三个目录 62 MB，全目录更大） |
| qiansai/.venv/ | 70 MB | 工作流环境 |
| qiansai/data、docs、third_party、docker、src、tests、scripts、configs | ~7 MB | 代码、数据与文档 |
| qiansai_*.bundle 等 4 个 git bundle + 两个导出文件 | ~4.5 MB | 历史会话备份 |
| qiansai/.venv-vllm | 符号链接 | 指向系统盘 /root/qiansai-envs/vllm-0.19.1 |

系统盘 /（30 GB，用 11 GB，余 20 GB）：
/root/qiansai-envs/vllm-0.19.1 为 10 GB（GPU 环境），
/root/miniconda3 为 7.5 GB，/root/.cache 116 MB。

工具：git 2.34.1、rsync、iverilog、vvp 在位；
uv 在非交互 PATH 中未找到（与 20260911 记录的"裸 python 不在 PATH、
使用 /root/miniconda3/bin/python"一致，登录 shell 可能可用）；
对本次迁移无影响，A100 侧自带 uv。

### 对迁移计划的影响

- 此前"数据盘约 20 GB 未记录用量"已定位：runs/ 实为 2.7 GB、
  model/ 实为 17 GB（权重 8.5 GB×2），加 .venv 与 bundle 与 df 对账一致。
- 需要传输的主体：qiansai/ 排除 .venv、.venv-vllm 后约 17 GB
  （权重为绝对大头）；runs/ 2.7 GB 可选，本地另有备份，可后补。
- 旧服务器 rsync 在位，A100 主动拉取方案可行。

## 文件、验证与发布

- 新增 runs/20260922_113600_autodl_disk_audit/（audit_output.txt、
  audit_commands.txt），凭据未写入。
- 新增本 journal。未修改源码、依赖锁、模型清单、子模块与既有文档；
  服务器上仅执行只读命令。
- 本轮未执行 git commit/push，待用户确认后发布。
