# 上下文与术语

本文件维护当前事实。目标和取舍见 [decisions.md](decisions.md)，历史见 [journal/](journal/)。

## 项目背景

- 仓库：https://github.com/fusang991/qiansai
- 赛事：全国大学生嵌入式芯片与系统设计竞赛 2026，AMD 3.1 本地智能体设计赛道。
- 当前选择：RTL，目标语言 Verilog / SystemVerilog。
- 路线：本地架构 → 32 GB NVIDIA 云服务器原方案部署 → AMD 迁移。
- 第一份开发数据：VerilogEval v2 的 dataset_spec-to-rtl，共 156 题。
- 已观察到原始 Prob031_dff 题面将 q 列为 input，参考接口为 output；保持固定数据不改写，评测时单独解释。
- 赛题依据：[原始 PDF](references/amd_2026_guide.pdf)。后续细则与镜像发布后单独登记版本。

## 常用名词

| 名词 | 本项目中的含义 |
| --- | --- |
| V / V-4B | core12345/ChipMATE-V-4B，Verilog 生成模型 |
| P / P-4B | core12345/ChipMATE-P-4B，Python 参考模型生成模型 |
| 双 4B | 两份独立权重协作，最终在同一张 GPU 的总显存预算内运行 |
| 上游 / 原版 | third_party/chipmate 固定提交中的生成与交叉验证流程 |
| 自验证 / 交叉验证 | 两份生成实现接受相同输入后的输出一致性检查 |
| 独立评测 | 用生成流程之外的参考实现和测试台判断候选代码 |
| 裸跑基线 | 同一 V-4B 权重、同一服务与上下文，题目直接生成一次，绕过技能与工具 |
| pass@1 / pass@5 | 需注明采样单位与评测器；上游的一个样本是完整多轮工作流 |
| journal | 一次工作一份日志，按时间与关键词命名，保留历史 |
| run | 一次可追踪的执行，其输入、输出、配置、版本和日志组成一个产物目录 |

## 环境事实：2026-09-11 本机检查

- 当前开发目录为 WSL2 工作区。
- GPU：NVIDIA GeForce RTX 4060 Laptop GPU，8188 MiB 显存。
- Icarus Verilog 12.0 和 vvp 可用；Python 3.13.5、uv 0.9.18 可用。
- Docker Desktop 命令入口存在，但当前 WSL 发行版未启用 Docker 集成，docker version 失败。
- 尚未下载两份模型权重，尚未进行本地或云端 GPU 推理测试。
- 以上是本地架构阶段的检查；当前已进入下述云端部署阶段。

## 环境事实：2026-09-11 云服务器

- Ubuntu 22.04.5 云平台容器，RTX 4080 SUPER，32760 MiB，驱动 595.71.05，计算能力 8.9。
- 数据盘挂载 /root/autodl-tmp，容量 50 GB；系统盘约 30 GB；/dev/shm 约 31 GB。
- 项目位于服务器 /root/autodl-tmp/qiansai。Python 3.12.3，uv 0.9.18，Icarus 已可用。
- .venv 是工作流环境；.venv-vllm 指向独立 GPU 环境，服务器预装环境保留。
- 服务器无 Docker 命令或 socket，先在平台现有容器中使用同一套脚本。
- 两份模型的 HF 访问权限已于 12:32 在服务器验证通过；凭据不进入项目记录。
- 用户 12:39 恢复部署，权重下载和 GPU 依赖安装直接在服务器后台执行。
- 两份权重已下载并校验 SHA256，每份 9,078,620,536 字节；各记录 9 个快照文件。
- 非交互入口已自动使用对应 Python 环境；本地、服务器均通过 22 项 pytest（CPU 检查）。
- GPU 环境 176 包兼容性检查通过，Torch 2.10.0 / CUDA 12.8 的 BF16 GPU 运算通过；vLLM 0.19.1、Transformers 5.5.3。
- 真实双模型验收已完成：Prob001_zero、Prob007_wire、Prob034_dff8 均通过官方 Icarus 编译和仿真。
- 该次每秒采样显存最大值 29209 MiB（28.52 GiB），命令结束后恢复到 1 MiB。
- 完整运行 474.97s；V/P 启动分别 215.27s / 191.21s，三题生成与评测分别 28.42s / 16.57s / 20.36s。
- 这是三题部署检查，不是全量 156 题通过率或论文 pass@k 复现；自有 Docker/AMD/Vivado 尚未验收。
- 后续初版全量运行已完成：14:08:04 至 17:08:30，全部 156 题逐题执行一次原版工作流，
  原始独立判定 109 PASS / 47 FAIL，ERROR / NOT_RUN 均为 0；通过占比 69.87%。
- 全量运行使用提交 0870769 的干净工作区；耗时 10825.27 秒，V/P 启动合计 116.23 秒，
  单题中位数 38.85 秒；显存每秒采样最大值 30201 MiB（29.49 GiB），结束后 1 MiB。
- 47 个原始 FAIL 分类为 35 个输出不匹配、10 个编译失败、2 个官方测试台超时。
  其中 12 题上游自验证一致率为 1.0，仍未通过官方评测。
- 19:35 在相同服务器、Icarus 11.0 下做官方参考实现 CPU 对照，151 PASS / 5 FAIL。
  Prob099_m2014_q6c 的参考端口与测试台不一致；Prob151_review2015_fsm 和
  Prob156_review2015_fancytimer 的参考枚举转换不受当前 Icarus 支持；
  Prob082_lfsr32 与 Prob141_count_clock 的测试台在参考实现零不匹配时仍触发时限。
  这五题需单独解释；保留原始 109/156 结果，没有事后删题或改写官方子模块。
- 证据：[访问复核](journal/20260911_123239_model_access_retry.md)、
  [恢复部署](journal/20260911_123913_cloud_resume.md)、
  [全量结果与参考对照](journal/20260911_193029_full_suite_results.md)。

## 比赛环境与待确认项

根据当前 PDF：AMD 验证资源为 W7900，最终部署验证为 R9700；方案需要满足单卡
32 GB、离线容器运行。最终 RTL 判定使用 Vivado 2025.2，目标器件
xczu3eg-sbva484-1-e，时钟约束 5 ns。Vivado 当前阶段暂缓。

指南 3.1.5.5 已列出评分权重：能力 30、同模型裸跑增益 40、墙钟效率 10、
智能体与技能包工程质量 20。具体公式、分级权重、阈值、采样和预算以后续评分细则为准。
指南还要求基线与智能体结果在同一次运行中产出，正式评测使用私有题集与 Vivado 分级判定。

待取得或确认：官方基础镜像、单题输入输出协议、时间预算与新版评分细则、
双模型基线的正式定义、第三方 Icarus 工具是否允许打包、实测可用的 CUDA/ROCm 镜像。
2026-09-11 官网内容接口返回 401，未能核实新版细则，不等于断言官方尚未发布。
依据和细节见 [比赛规则解读](competition.md)与
[本轮规则核对](journal/20260911_222729_competition_review.md)。

## 版本登记

- ChipMATE：d94087b5159aea482648b26398a2ffb164246671。
- VerilogEval：c498220d0a52248f8e3fdffe279075215bde2da6（v2.0.0）。
- V-4B revision：7fbb17249a49d109787bbc024a7a21b83302a1c2。
- P-4B revision：cf59695163ad3e4b63bcc6c4eaa91b05fedc4a2e。
- 权重身份及已校验的权重 SHA256 见 [manifest](../model/manifest.json)；完整文件清单保存在下载产物中。
- 此处的参数规模与作者报告不是本项目的显存或通过率实测。
