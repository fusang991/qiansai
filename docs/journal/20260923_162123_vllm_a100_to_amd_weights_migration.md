# 2026-09-23 16:21:23 CST — vLLM A100 → AMD 迁移咨询（权重与注意事项）

## 用户原始请求

> 我们现在是在 a100 上使用，之后迁移到 amd上。 我们现在是docker 里面创建了一个 vllm 的环境，
> 然后这个image再使用我们的harness 代码， 那 就是比如大模型的weight 到时候怎么迁移，
> 迁移还有什么要注意的吗？ 因为我注意到 vllm 也有 amd 适配的image，所以感觉方法是合理的

## 环境与工具状态（本次会话可观测事实）

- `TZ=Asia/Shanghai date` 返回 `2026-09-23 16:21:23 CST`（该次调用因沙箱后端不可用，需以
  danger-full-access 模式重试才成功）。
- `web_search` 调用失败：`Authentication Fails, your api key: ****5703 is invalid`。
  因此本次回答**未能联网核实** vLLM ROCm 镜像的具体 tag 与最新版本，回答基于既有知识，
  具体 tag / ROCm 版本号需用户自行到 Docker Hub / vLLM 官方文档确认。
- 未修改任何代码、配置或子模块；本次会话仅产出本 journal 条目。

## 助手面向用户的回答要点

1. **权重本身基本不需要“迁移”**：HuggingFace `safetensors` 权重与硬件无关，
   A100 上的权重文件可原样在 AMD 卡上加载，不存在 NVIDIA → AMD 的权重格式转换。
   迁移的实际工作是**传输 + 校验 + 换镜像/运行时**。
   - 传输：共享盘/NFS、`rsync`、`hf download` 重新下载、对象存储；
   - 校验：记录 sha256 与 repo/revision 到 manifest（符合 AGENTS.md “权重不进 Git，
     用 manifest 记录身份”的约定）。
2. **例外（需要注意的权重相关事项）**：
   - 量化权重（GPTQ / AWQ / FP8 / Marlin）在 ROCm 上的内核支持面比 CUDA 小，
     需逐个确认目标模型在 ROCm build 中有对应实现，否则回退慢路径或需重新量化；
   - A100 (Ampere) 不支持 FP8 计算，如果当前部署是 bf16/fp16，则权重可直接复用；
     若想借迁移切换到 FP8（MI300X 支持），属于**另一次数值基线变化**，应单独评估；
   - 若此前用 CUDA 专用工具做过转换/量化，需在 AMD 侧用对应工具链复核。
3. **镜像层**：CUDA image → ROCm image 是迁移的核心。要点：
   - 官方/社区确有 ROCm 版 vLLM 镜像（用户观察正确，方法合理），但：
   - 宿主机 amdgpu 驱动 + ROCm 版本必须与镜像内 ROCm 版本匹配（ROCm 比 CUDA 更敏感）；
   - ROCm build 的发版通常落后 CUDA build，版本 pin 策略要改写；
   - ROCm build 的模型/算子覆盖面 < CUDA build，目标模型要单独验证。
4. **容器启动差异**：NVIDIA 的 `nvidia-container-toolkit`/`--gpus` 换成
   `--device=/dev/kfd --device=/dev/dri --group-add video --group-add render` 一类参数；
   非官方数据中心卡可能需要 `HSA_OVERRIDE_GFX_VERSION`；性能排查涉及
   `PYTORCH_HIP_ALLOC_CONF`、attention backend 选择等环境变量。
5. **harness 层**：OpenAI 兼容 API 不变，推理服务接口大概率零改动；要检查的是
   GPU 探测（`nvidia-smi`、`CUDA_VISIBLE_DEVICES`）、健康检查、镜像 tag 与版本 pin、
   启动脚本里的 CUDA 假设。
6. **数值与结果**：AMD 与 NVIDIA 不会 bit-exist 一致，采样结果、KV cache、
   CUDA graph/hipGraph 差异都会带来扰动。现有 156 题 109 PASS / 47 FAIL 的结果
   **需要在 AMD 上重新建立基线**，并把“硬件数值差异”与已知的 5 个 evaluator limitation
   区分开；原始 runs 保留不覆盖。
7. 建议的迁移顺序：AMD 机器装驱动/ROCm → 拉 ROCm 镜像 → 传权重并校验 →
   跑同一 smoke 脚本（pytest）→ 对比 PASS/FAIL 分布 → 再考虑性能与量化优化。

## 待办 / 未决

- 用户尚未告知目标 AMD GPU 型号（MI300X / MI250 / 消费卡），影响镜像与驱动选型。
- vLLM ROCm 镜像 tag 与支持模型矩阵需联网核实（本次会话 web_search 认证失败）。

## 追加：用户回复目标显卡

用户原话：

> 消费级 RX 7900 系， 好似32G

助手追加回答要点（`web_search` 重试仍因 API key 认证失败，未能联网核实）：

1. **显存对不上，需用户核实**：RX 7900 系公开型号为 XTX 24 GB / XT 24 GB / GRE 16 GB，
   没有 32 GB 版本；32 GB 的 RDNA3 卡是工作站卡 Radeon Pro W7800（同为 gfx1100）。
   建议用 `lspci -nn` / `rocm-smi` 确认具体 device id 与显存。
2. **消费卡不在 vLLM ROCm 官方支持范围**（官方面向数据中心 MI 系列），需要
   `HSA_OVERRIDE_GFX_VERSION=11.0.0` 之类覆盖才能跑 gfx1100，属"能跑但自负风险"，
   算子回退、attention backend 受限、发版支持滞后都可能出现。
3. **显存是硬约束**：24 GB 装不下 14B 级 bf16 权重（约 28 GB），7~8B bf16 可行；
   更大模型只能靠量化（AWQ/GPTQ 在 ROCm 消费卡上的内核覆盖需逐个验证）。
4. **FP8 不可行**：上一轮"可切 FP8"的建议只对 MI300X 成立，7900 系请继续 bf16/fp16。
5. **多卡 P2P 受限**：消费级 RDNA3 双卡基本没有可用的 P2P/RCCL 互联，
   张量并行不现实，单卡跑就是上限。
6. 备选：若 vLLM ROCm 在 gfx1100 上受阻，可考虑暴露同一 OpenAI 兼容 API 的
   替代服务（llama.cpp server 等），对 harness 的推理服务接口层透明。
