# 上下文与术语

本文件维护当前事实。目标和取舍见 [decisions.md](decisions.md)，历史见 [journal/](journal/)。

## 项目背景

- 仓库：https://github.com/fusang991/qiansai
- 赛事：全国大学生嵌入式芯片与系统设计竞赛 2026，AMD 3.1 本地智能体设计赛道。
- 当前选择：RTL，目标语言 Verilog / SystemVerilog。
- 路线：本地架构 → 32 GB NVIDIA 云服务器原方案部署 → AMD 迁移。
- 第一份开发数据：VerilogEval v2 的 dataset_spec-to-rtl，共 156 题。
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
- 用户已说明后续提供 32 GB 显存的 NVIDIA 云服务器；当前只完善本地架构。

## 比赛环境与待确认项

根据当前 PDF：AMD 验证资源为 W7900，最终部署验证为 R9700；方案需要满足单卡
32 GB、离线容器运行。最终 RTL 判定使用 Vivado 2025.2，目标器件
xczu3eg-sbva484-1-e，时钟约束 5 ns。Vivado 当前阶段暂缓。

待取得：官方基础镜像、单题输入输出协议、最终时间预算和评分细则、模型下载访问权限、
实测可用的 CUDA/ROCm 镜像版本、云机器环境信息。

## 版本登记

- ChipMATE：d94087b5159aea482648b26398a2ffb164246671。
- VerilogEval：c498220d0a52248f8e3fdffe279075215bde2da6（v2.0.0）。
- 权重 revision：待首次授权下载前固定，见 [manifest](../model/manifest.json)。
- 此处的参数规模与作者报告不是本项目的显存或通过率实测。
