# 2026-09-11 12:32:39 + model_access_retry

- 时区：Asia/Shanghai；时间为本轮验证完成后的记录时间。
- 范围：用户暂停部署后，仅重新验证两份固定版本模型的访问权限。
- 前置记录：[部署工作](20260911_120416_cloud_deployment.md)。此前部署日志与核心文档的完整收尾仍待恢复工作。
- 本轮没有恢复依赖安装、下载权重、启动模型、修改业务代码或提交推送。
- 认证使用用户此前提供的凭据。本文不保存密码、token 或签名下载链接。

## 用户原始输入

前一轮暂停：

> 先停一下，汇报一下进度和问题

本轮：

> ok了，你再试一下模型能否访问

## 助手用户可见回复

1. 我用服务器上已保存的 token 重新检查两份模型的访问权限，本次只验证访问。
2. 此前的 SSH 复用连接已断开，新连接也被服务器关闭了。我先重新建立连接，确认保存的 token 能否读取模型文件。

## 操作和结果

1. 原 SSH 复用路径未能继续使用；BatchMode 连接返回 Permission denied (publickey,password)。
2. 首次重建连接返回 Connection closed；再次连接核对已知主机密钥后，使用此前密码认证成功。
3. 同时在本地使用只驻留进程内存的 token 验证，两份模型均返回 ACCESS_OK。
4. 在服务器启用其已有网络加速配置，使用仓库外 HF 标准登录缓存重新验证，两份均返回 ACCESS_OK。
5. 实际调用 HfApi.model_info 与 get_hf_file_metadata，针对固定 revision 检查 config.json 和 model.safetensors。
   没有下载 model.safetensors 的正文；返回大小来自文件元数据，不表示已下载。

服务器原始检查输出：

```json
{"model": "core12345/ChipMATE-V-4B", "status": "ACCESS_OK", "revision": "7fbb17249a49d109787bbc024a7a21b83302a1c2", "weight_file": "model.safetensors", "weight_file_bytes": 9078620536}
{"model": "core12345/ChipMATE-P-4B", "status": "ACCESS_OK", "revision": "cf59695163ad3e4b63bcc6c4eaa91b05fedc4a2e", "weight_file": "model.safetensors", "weight_file_bytes": 9078620536}
```

## 当前结论

- 更正此前“两份模型均返回 403”的状态：本轮本地和服务器均已通过访问检查。
- 权限障碍已解除；双模型加载、显存、速度与真实 testcase 结果仍未验证。
- GPU 依赖安装仍按用户暂停要求停止，未启动新的安装或下载进程。
- 本轮只新增本日志；此前未提交的业务修改保留，未重新运行 pytest 或 Docker 检查。

## 交付答复

可以了，已在服务器确认 **V-4B 和 P-4B 均可访问**，配置文件和权重文件的权限检查都通过，之前的 403 已解决。

本次仅验证访问，安装和下载仍保持暂停。
