# 模型声明

| 角色 | 模型 | 来源 |
| --- | --- | --- |
| Verilog | ChipMATE-V-4B | https://huggingface.co/core12345/ChipMATE-V-4B |
| Python | ChipMATE-P-4B | https://huggingface.co/core12345/ChipMATE-P-4B |

作者说明基座为 Qwen3.5-4B，公开模型页标注最终多智能体训练阶段的 BF16 权重。
两份模型目前有 Hugging Face 访问条件，需要账号取得访问权限。认证信息只通过本机环境
或 Hugging Face 登录缓存提供，不进入 Git。

当前权重未下载，revision、文件 SHA256、实测显存、速度和通过率尚未填入。
首次下载前在 manifest.json 固定具体 revision；下载脚本拒绝 main 等浮动版本。
下载后在本地 weights/download_manifest.json 保存各文件 SHA256，再将需要分享的
版本证据写入工作日志。

serving.yaml 的上下文和内存配置是首次云端实验的起点。
最终要报告两个模型同时工作时的总显存，包括缓存与工作空间。
作者的 24 GB 可容纳说明不能替代本项目对 32 GB 目标环境的实测。
