# 模型声明

| 角色 | 模型 | 来源 |
| --- | --- | --- |
| Verilog | ChipMATE-V-4B | https://huggingface.co/core12345/ChipMATE-V-4B |
| Python | ChipMATE-P-4B | https://huggingface.co/core12345/ChipMATE-P-4B |

作者说明基座为 Qwen3.5-4B，公开模型页标注最终多智能体训练阶段的 BF16 权重。
两份模型目前有 Hugging Face 访问条件，需要账号取得访问权限。认证信息只通过本机环境
或 Hugging Face 登录缓存提供，不进入 Git。

两份 revision 已固定到 manifest.json，已在 NVIDIA 服务器完成下载和 SHA256 校验。
下载脚本拒绝 main 等浮动版本；已完成三题 NVIDIA 部署验收和一次全量 156 题运行。
服务器 weights/download_manifest.json 保存各文件 SHA256，再将需要分享的
版本证据写入工作日志。

serving.yaml 的 BF16 / 16384 上下文 / 单服务 0.45 显存比例已用于初版全量实验。
两模型同时工作的设备显存每秒采样最大值为 30201 MiB（29.49 GiB），包括缓存与工作空间；
这不是连续观测的瞬时峰值，也不能替代 AMD 或其他负载的测试。
作者的 24 GB 可容纳说明不能替代本项目对 32 GB 目标环境的实测。

当前两份固定 revision 的官方元数据均报告 model.safetensors 为 9,078,620,536 字节；
这是下载体积信息，不是运行显存测量。

全量原始独立判定 109/156 通过；参考实现 CPU 对照发现 5 题存在评测条件问题。
两份模型权重及版本未因结果变化而调整。

证据：[部署与三题验收](../docs/journal/20260911_123913_cloud_resume.md)、
[全量运行与参考对照](../docs/journal/20260911_193029_full_suite_results.md)。
