# 容器部署契约

当前 CUDA Dockerfile、Compose 与启动脚本是后续云部署使用的模板。
本机 Docker Desktop 的 WSL 集成不可用，镜像构建和 GPU 推理尚未验证。

1. 从支持 ChipMATE 权重架构的 vLLM CUDA 镜像出发，固定 tag 或 digest。
   CUDA_VLLM_IMAGE 未设置时 Compose 明确报错，避免隐式使用 latest。
2. uv.lock 固定独立的工作流环境，镜像自带 vLLM 的 GPU 依赖保留在原环境中。
3. 一个容器启动 V/P 两个模型服务，两者共享映射进来的单张 GPU。
4. BF16、上下文、显存比例和并发来自 configs/serving.yaml，均待云卡实测。
5. 模型从 /models/chipmate-v-4b 与 /models/chipmate-p-4b 本地加载。
   离线环境变量控制模型资源访问；完整断网验收仍需在网络沙箱中实际执行。
6. 使用 docker compose exec qiansai bash run.sh ... 调用已有服务。

服务端口约定为 8001/8002，宿主机默认只绑定 127.0.0.1，可通过 SSH 转发。
脚本不安装宿主机驱动，不管理云机器权限，不修改 Docker Desktop 设置。
AMD 阶段再添加 Dockerfile.rocm 与 compose.rocm.yaml，复用相同入口和接口。
最终以官方基础镜像重建单容器，按正式规则验证显存、功能、耗时和离线运行。

参考：

- https://docs.vllm.ai/en/latest/deployment/docker/
- https://docs.docker.com/compose/how-tos/gpu-support/
- https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.2/how-to/docker.html
