# 2026-09-11 11:12:34 + repository_setup

- 时区：Asia/Shanghai。
- 类型：本次工作。
- 起始状态：目录只有赛题 PDF，Git 元数据目录为空；目标 GitHub 仓库为空。
- 关联历史：[架构讨论](20260911_111234_architecture_history.md)。

## 用户原始输入

> ok，你先把整个架构按照这个写。然后push 到https://github.com/fusang991/qiansai

中途补充：

> 补充一句，在本地部署好后。我会把云服务器32G 显存的密码给你, 你不用担心，现在就是本地把架构做好

测试偏好：

> 对，如果要写test，我觉得就用pytest

## 助手进度回复

1. 我会把选定的目录、三份核心文档、逐次工作日志和部署约定落到仓库里，固定 ChipMATE 与 VerilogEval 的版本，检查后提交并推送到你指定的 GitHub 仓库。部署状态会如实记录，目前尚未实测的 GPU 环境会明确标注。
2. 目标 GitHub 仓库目前为空，本地 Git 已初始化。接下来会把上游代码和数据集作为固定版本的子模块加入，并将此前的架构讨论补录到日志中。当前本机只有 8 GB 显存，本次会完成仓库与部署入口，不把双 4B 推理标记为已跑通。
3. 明白，32 GB 云服务器的模型部署留到后续。本次专注把本地架构、文档、数据和版本管理做好并推送。ChipMATE 和 VerilogEval 已拉取，官方 RTL 数据集确认有 156 道题。
4. 文档结构已落盘，赛题 PDF 也已移到 docs/references/，文件内容的校验和保持不变。我正在补齐轻量运行入口和检查脚本；Docker 配置会要求显式指定镜像版本，避免未验证的环境被误当成可复现环境。
5. 收到，测试统一用 pytest。我会把数据适配和 Icarus 检查放进 pytest，smoke_test.sh 只负责调用这些检查，不另建测试框架。
6. 156 道题已转换为 ChipMATE 可读输入，生成输入中只保留题目和接口声明。pytest 的数据适配与 Icarus 检查也已加入，接下来执行验证、补齐历史日志并检查待提交内容。

## 操作与结果

| 操作 | 结果 |
| --- | --- |
| git status --short --branch | 初始不是 Git 仓库 |
| git ls-remote https://github.com/fusang991/qiansai.git | 沙箱内 DNS 失败，升级执行后成功，远端没有引用 |
| git init -b main | 成功；Git 元数据只读限制通过正常提权处理 |
| git remote add origin https://github.com/fusang991/qiansai.git | 成功 |
| git submodule add https://github.com/zhongkaiyu/ChipMATE.git third_party/chipmate | 成功，固定 d94087b5159aea482648b26398a2ffb164246671 |
| git submodule add https://github.com/NVlabs/verilog-eval.git data/verilog_eval | 成功，固定 c498220d0a52248f8e3fdffe279075215bde2da6 |
| 原始数据计数 | 156 题目、156 参考实现、156 测试台 |
| Docker version | 当前 WSL 未启用 Docker Desktop 集成；未构建或运行镜像 |
| 公开 HF 模型元数据读取 | 两次 curl 均发生 TLS 错误；未取得 revision，清单保持 null |
| PDF 移动至 docs/references/amd_2026_guide.pdf | SHA256 移动前后相同 |
| uv lock --default-index https://pypi.org/simple | 固定 33 个轻量依赖包 |
| python3 scripts/prepare_data.py | 成功生成 156 道接口化题目及清单 |

PDF SHA256：
5d2ac935c22ea61ab134c2c15a2f05ae26e89dd90367eb0d553cff23a37a5a24。

生成 JSONL SHA256：
f0813c4aea80b0954cb393f5a6329db487eb88340a0a17e51d2bec7179d46273。

编辑工具调用曾因模板字符串中的 shell 插值发生两次构造错误，未产生对应文件修改；
修正调用文本后重新提交补丁成功。没有修改上游算法。

## 决策及实现边界

- 按用户最新要求，当前只完成本地架构与推送；后续再使用用户提供的 32 GB 云服务器。
- 三份共识文档与逐次 journal 已建立，旧讨论在独立历史补录中保存。
- 测试框架统一为 pytest，并写入 AGENTS.md、decisions.md 和开发依赖。
- CUDA 文件提供模板和明确入口；镜像版本要求显式选择，不使用浮动 latest。
- ROCm、Vivado、独立评分和完整模型调用追踪按阶段预留，不伪造完成状态。
- 模型访问条件与 revision 未解决，不在本阶段下载权重。
- 同模型基线单次调用，不使用技能、反馈工具或模型重试。
- 原版工作流通过薄适配调用，上游默认输出上限保留 4096。
- 参考实现仅在离线数据转换时抽取接口，生成输入不含参考逻辑正文。

## 验证、提交和推送

最终 pytest 输出、仓库检查与发布结果在本条后续补充中记录。
命令输出归档和最终提交信息不以尚未执行的结果预填。

### 本地验证完成

安装命令：uv sync --frozen --default-index https://pypi.org/simple。
解析锁定 33 个包，当前平台安装 31 个包；pytest 版本为 9.1.1。
没有安装 vLLM、CUDA 或 ROCm，也没有下载模型权重。

运行命令：bash scripts/smoke_test.sh -q。

```text
{
  "dataset_revision": "c498220d0a52248f8e3fdffe279075215bde2da6",
  "task": "spec-to-rtl",
  "count": 156,
  "input_sha256": "f0813c4aea80b0954cb393f5a6329db487eb88340a0a17e51d2bec7179d46273",
  "reference_body_in_generation_input": false
}
......                                                                   [100%]
6 passed in 0.34s
```

六项测试包括：保留接口而去掉参考正文、拒绝不支持的非 ANSI 接口、156 题完整转换、
重复题号拒绝、Icarus/Python 输出一致正例、输出不一致反例。

其他检查：

- 对五个 shell 脚本逐个运行 bash -n，全部通过。
- 解析自有 Python 文件的 AST、YAML 配置，全部通过。
- README 与三份核心文档的当前本地链接存在。
- run.sh --help、run_baseline.sh --help、fetch_models.py --help 均正常。
- 独立评分尚未实现，Docker/GPU 检查未执行，不能把六项 CPU 测试解释为模型已部署。

助手进度回复：

> 本地检查已通过：6 个 pytest 测试全部通过，覆盖数据接口提取和 Icarus 正反例；脚本语法、配置解析及文档链接也正常。现在进行提交前检查，随后推送到 fusang991/qiansai 的 main 分支。
