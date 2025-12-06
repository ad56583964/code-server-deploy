# code-server 快速部署工具（Ubuntu 24.04）

这个仓库用于在 **Ubuntu 24.04** 上快速部署带自签名 HTTPS 的 code-server。

包含内容：

- `scripts/gen_self_signed_cert.py`：生成自签名 TLS 证书（兼容 code-server，带 SAN）
- `Makefile`：封装依赖安装、code-server 安装、证书生成、systemd 配置

## 推荐执行顺序

1. 克隆仓库并进入目录

   ```bash
   git clone git@github.com:ad56583964/code-server-deploy.git
   cd code-server-deploy
   ```

2. 安装系统依赖（Python / openssl / curl / wget / make / git）

   ```bash
   make install-deps
   ```

3. 按需修改 `.env.toml`

   - `[code_server]`：版本、端口
   - `[cert]`：域名（`domain`）、证书输出目录（`out_dir`）、有效期等

4. 一键部署 code-server（推荐）

   ```bash
   make deploy HOST=my.code-server.local CODE_SERVER_PASSWORD='你的强密码'
   ```

   - `HOST`：覆盖 `.env.toml` 中的域名（不传则用 `.env.toml` 里的 `cert.domain`/`cert.host`）
   - `CODE_SERVER_PASSWORD`：code-server 登录密码（写入 systemd override）

   这个流程在执行 `setup-systemd` 时会：

   - 停止并禁用 / mask 旧的系统级 `code-server.service`（如果存在）
   - 重启并启用基于模板的 `code-server@<user>` 服务

5. 或者手动分步执行

   ```bash
   # 安装 code-server（默认版本见 .env.toml）
   make install-code-server

   # 生成并安装自签名证书（默认域名和路径见 .env.toml）
   make install-cert HOST=my.code-server.local

   # 配置 systemd 并设置登录密码
   make setup-systemd CODE_SERVER_PASSWORD='你的强密码'
   ```

## 访问方式（默认启用 HTTPS）

部署完成后，这套流程会：

- 使用 `install-cert` 在 `~/.config/code-server` 下生成 `cert.pem` / `key.pem`
- 使用 `install-config` 生成 `config.yaml`，其中包含：
  - `bind-addr: 0.0.0.0:<port>`
  - `cert` / `cert-key` 指向上述证书文件

code-server 启动时会自动读取 `~/.config/code-server/config.yaml`，检测到 `cert` / `cert-key` 后 **默认启用 HTTPS**。

因此部署完成后，通常可以通过以下地址访问（根据你的 HOST/端口调整）：

```text
https://my.code-server.local:8080
```

因为是自签名证书，浏览器第一次访问会有安全提示，需要手动确认继续访问或手动信任该证书。
