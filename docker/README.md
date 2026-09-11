# 容器部署契约

CUDA Dockerfile、Compose 尚未构建验证。本机 Docker Desktop 的 WSL 集成不可用；
当前云服务器自身是平台容器，没有 Docker 服务，使用以下同源脚本先验证推理环境。

1. 从支持 ChipMATE 权重架构的 vLLM CUDA 镜像出发，固定 tag 或 digest。
   CUDA_VLLM_IMAGE 未设置时 Compose 明确报错，避免隐式使用 latest。
2. uv.lock 固定独立的工作流环境，镜像自带 vLLM 的 GPU 依赖保留在原环境中。
3. 一个容器启动 V/P 两个模型服务，两者共享映射进来的单张 GPU。
4. BF16、上下文、显存比例和并发来自 configs/serving.yaml，已在平台现有 NVIDIA 容器完成三题验收。
   自有镜像和 AMD 执行仍需各自验证。
5. 模型从 /models/chipmate-v-4b 与 /models/chipmate-p-4b 本地加载。
   离线环境变量控制模型资源访问；完整断网验收仍需在网络沙箱中实际执行。
6. 使用 docker compose exec qiansai bash run.sh --case Prob001_zero 调用已有服务。

平台现有容器/宿主机：

```bash
bash scripts/setup_cuda.sh
.venv/bin/hf auth login
.venv/bin/python scripts/fetch_models.py
./run.sh --case Prob001_zero
```

依赖约束集中在 requirements.cuda.txt，完整版本与哈希固定在 requirements.cuda.lock；
安装脚本使用后者并执行 uv pip check。.venv-vllm 与工作流 .venv 独立。
GPU 安装脚本支持 QIANSAI_PYPI_INDEX 指定包索引，QIANSAI_PYTHON 指定 Python 3.12。
uv.lock 包含官方文件地址；受限网络可由 uv export --frozen 导出 requirements，
通过镜像按锁定版本和哈希安装，仍需复核与 uv.lock 一致。

docker/entrypoint.sh 与 scripts/serve_models.sh 共用 qiansai.services。
它检查本地模型下载清单和分片完整性，从本地加载权重，启动两个服务并等待健康状态。
需要反复运行 testcase 时，在独立终端保持 serve_models.sh 运行；run.sh 自动复用服务。

服务端口约定为 8001/8002，宿主机默认只绑定 127.0.0.1，可通过 SSH 转发。
脚本不安装宿主机驱动，不管理云机器权限，不修改 Docker Desktop 设置。
AMD 阶段再添加 Dockerfile.rocm 与 compose.rocm.yaml，复用相同入口和接口。
最终以官方基础镜像重建单容器，按正式规则验证显存、功能、耗时和离线运行。

参考：

- https://docs.vllm.ai/en/latest/deployment/docker/
- https://docs.docker.com/compose/how-tos/gpu-support/
- https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.2/how-to/docker.html
