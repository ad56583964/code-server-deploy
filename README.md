# code-server 快速部署工具（Ubuntu 24.04）

这个仓库用于在 **Ubuntu 24.04** 上快速部署带自签名 HTTPS 的 code-server。

包含内容：

- `scripts/gen_self_signed_cert.py`：生成自签名 TLS 证书（兼容 code-server，带 SAN）
- `Makefile`：封装安装、生成证书、配置 systemd 的快捷命令

## 使用前准备

```bash
sudo apt update
sudo apt install -y make python3 openssl curl wget
```

## 常用 Make 命令

```bash
# 查看可用目标
make help

# 1. 安装指定版本的 code-server（默认 4.102.3）
make install-code-server

# 2. 生成自签名证书（默认域名 code-server.local，输出到 ~/.config/code-server）
make cert
# 或指定域名：
make cert HOST=my.code-server.local

# 3. 配置 systemd 服务并设置登录密码（必须提供密码）
make setup-systemd CODE_SERVER_PASSWORD='你的强密码'

# 一步完成安装 + 证书 + systemd
make deploy HOST=my.code-server.local CODE_SERVER_PASSWORD='你的强密码'
```

执行完成后，通常可以通过以下地址访问（根据你的 HOST/端口调整）：

```text
https://my.code-server.local:8080
```

如果是自签名证书，浏览器第一次访问会有安全提示，需要手动确认继续访问。

