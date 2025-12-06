# 在新机器安装 code-server（含自签名 HTTPS）简要流程

> 适用环境：Ubuntu 22.04+/systemd，使用普通用户运行 code-server，通过自签名证书提供 HTTPS（例如 `code-server.local`）。

下面步骤默认：

- 用户名：当前登录用户（`$USER`）
- 端口：`8080`
- 域名：`code-server.local`（可以换成自己的域名）
- code-server 版本：`4.102.3`（与当前机器一致）

```bash
# 按需修改这些变量后再执行下面命令
export CODE_SERVER_VERSION=4.102.3
export CODE_SERVER_PORT=8080
export CODE_SERVER_HOST=code-server.local
export CODE_SERVER_USER="$USER"
export CODE_SERVER_PASSWORD='请改成自己的强密码'
```

## 1. 环境准备

```bash
sudo apt update
sudo apt install -y curl wget openssl
```

## 2. 安装 code-server（.deb 包）

```bash
cd /tmp
wget "https://github.com/coder/code-server/releases/download/v${CODE_SERVER_VERSION}/code-server_${CODE_SERVER_VERSION}_amd64.deb"

sudo dpkg -i "code-server_${CODE_SERVER_VERSION}_amd64.deb" || \
  sudo apt -f install -y

code-server --version
```

确认能看到版本号（例如 `4.102.3`）。

## 3. 生成自签名 HTTPS 证书

在运行 code-server 的用户下执行：

```bash
mkdir -p ~/.config/code-server/key

cat > ~/.config/code-server/key/key.conf <<EOF
[req]
prompt = no
default_bits = 4096
default_md = sha512
distinguished_name = dn
x509_extensions = v3_req

[dn]
C=CN
ST=Zhejiang
L=Hangzhou
O=Example
OU=Code Server
CN=${CODE_SERVER_HOST}
emailAddress=admin@example.com

[v3_req]
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName=@alt_names

[alt_names]
DNS.1 = ${CODE_SERVER_HOST}
EOF

cd ~/.config/code-server

openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 \
  -config key/key.conf \
  -keyout key.pem \
  -out cert.pem
```

生成后，证书和私钥位置为：

- 证书：`~/.config/code-server/cert.pem`
- 私钥：`~/.config/code-server/key.pem`

## 4. 配置 code-server

```bash
cat > ~/.config/code-server/config.yaml <<EOF
bind-addr: 0.0.0.0:${CODE_SERVER_PORT}
auth: password
cert: ${HOME}/.config/code-server/cert.pem
cert-key: ${HOME}/.config/code-server/key.pem
EOF
```

说明：

- `bind-addr` 为 `0.0.0.0:端口`，表示监听所有网卡；需要固定某个内网 IP 时可改成对应 IP。
- 认证方式为密码（密码下一步在 systemd 中通过环境变量传入）。

## 5. 配置 systemd 服务与自启动

`code-server` 的 .deb 包已经安装好 systemd 模板服务 `code-server@.service`，这里为它配置密码并启用自启动。

```bash
sudo mkdir -p /etc/systemd/system/code-server@.service.d

sudo tee /etc/systemd/system/code-server@.service.d/override.conf >/dev/null <<EOF
[Service]
Environment=PASSWORD=${CODE_SERVER_PASSWORD}
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "code-server@${CODE_SERVER_USER}"
```

检查运行情况：

```bash
systemctl status "code-server@${CODE_SERVER_USER}" --no-pager
ss -lntp | grep "${CODE_SERVER_PORT}"
```

正常情况下，可以看到对应端口由 `node`/`code-server` 进程在监听。

## 6. 域名解析与访问

1. 把域名指向新机器 IP  
   - 内网测试：在客户端机器上编辑 `/etc/hosts`，例如：

     ```bash
     echo "192.168.x.x ${CODE_SERVER_HOST}" | sudo tee -a /etc/hosts
     ```

   - 公网域名：在域名服务商控制台设置 A 记录指向服务器公网 IP。

2. 浏览器访问：

   ```text
   https://<你的域名>:<端口>
   例如：https://code-server.local:8080
   ```

首次使用自签名证书，会有安全警告，需要在浏览器中选择“继续访问”或将证书加入信任。

