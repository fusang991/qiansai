# 2026-09-11 22:15:18 + Standalone server setup guide

- 时区：Asia/Shanghai
- 类型：本次工作，文档整理
- 起始版本：b79eed1253288ae961c78818cb5010e12b84b97e
- 关联运行目录：runs/20260911_221518_server_setup_guide/

## 用户原始输入

> 你最好单独写个md 记录一下你上面的内容

## 助手进度回复

我会单独写一份新服务器部署说明，列清本地、服务器和 Git 各有什么，以及 clone 后的准备步骤，并在 README 加上入口。

独立文档已写好，文件清单、部署步骤和运行命令都已整理进去。链接和 Bash 命令语法检查通过，现在推送到仓库。

## 操作与依据

- git status --short 起始输出为空。
- 读取 README.md、docs/context.md、docs/decisions.md、docs/architecture.md，
  以及 docs/journal/20260911_220716_clone_recovery.md；沿用已核对的文件范围和安装入口。
- 时钟工具返回 2026-09-11 14:15:18 UTC，文件名换算为 Asia/Shanghai。
- 新建 docs/guides/server_setup.md，独立保存用户要求的两端清单和新机器操作步骤。
  放在 guides/ 下，继续保留三份核心共识文档。
- 新文档包含 Git 与非 Git 文件的区别、基础软件前提、子模块获取、
  两个 Python 环境安装、权重下载/复制、三题与全量验收、历史产物恢复及已验证边界。
- README.md 添加文档入口；docs/architecture.md 添加操作手册链接和目录项。
- 不修改源码、依赖锁、模型或子模块，不连接旧服务器，不实际下载、部署或执行 GPU 任务。
  服务器事实引用已有核对记录，不记为本次实测。

## 验证与发布

- 检查 Markdown 本地链接、代码块 Bash 语法、暂存区差异、凭据特征与固定 gitlink。
  文档修改不重复 pytest、Docker、GPU、AMD 或 Vivado 验收。
- 实际检查命令、返回和 Git 发布结果保存在
  runs/20260911_221518_server_setup_guide/publication.json。
- 按用户已有的 Git 提交/推送授权发布文档；本提交通过 Git 历史追溯。
  旧服务器本轮未同步文档。

## 助手最终回复

已写好：[本地与新服务器部署说明](/home/young/autodl/qiansai/docs/guides/server_setup.md)。

包含两端文件清单、Git 能恢复的内容、新服务器安装步骤、权重复制／下载方式，以及三题和全量运行命令。README 已添加入口，文档已推送 GitHub。
