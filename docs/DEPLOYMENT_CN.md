# 国内公网部署步骤

这份文档面向“不熟悉线上部署，但希望别人能直接用浏览器访问”的场景。

## 结论

推荐方案：

1. 购买一台云服务器。
2. 绑定域名。
3. 用 Caddy 提供 HTTPS。
4. 用 systemd 长期运行 FastAPI。
5. 用 `REFRESH_TOKEN` 保护刷新接口。

如果主要用户在国内，长期方案优先选中国大陆地域云服务器；大陆服务器绑定域名通常需要完成 ICP 备案。没有备案前，可以先用中国香港地域过渡。

## 1. 购买服务器

选择任意主流国内云厂商的轻量云服务器即可，例如阿里云、腾讯云、华为云、火山引擎。

建议配置：

- 地域：长期选中国大陆；不想先备案可选中国香港过渡
- 系统：Ubuntu 22.04 LTS 或 Ubuntu 24.04 LTS
- 规格：1 核 1G 起步，2G 更稳
- 磁盘：20GB 以上
- 防火墙/安全组：开放 `22`、`80`、`443`

不建议直接开放 `8000` 给公网。`8000` 只给本机 Caddy 访问。

## 2. 准备域名

如果使用大陆服务器：

1. 购买域名。
2. 在云厂商控制台提交 ICP 备案。
3. 备案通过后，把域名解析到服务器公网 IP。

如果使用香港服务器：

1. 可以先跳过备案。
2. 直接把域名解析到服务器公网 IP。

DNS 记录示例：

```text
类型：A
主机记录：@
记录值：你的服务器公网 IP
```

如果要使用 `www.example.com`，再加一条：

```text
类型：A
主机记录：www
记录值：你的服务器公网 IP
```

## 3. 登录服务器

在本地终端执行：

```bash
ssh root@你的服务器公网IP
```

第一次登录后更新系统：

```bash
apt update
apt upgrade -y
```

安装基础工具：

```bash
apt install -y git python3 python3-venv python3-pip curl
```

## 4. 上传并安装项目

推荐把项目放到 `/opt/bj-presale-tracker`：

```bash
cd /opt
git clone <你的 Git 仓库地址> bj-presale-tracker
cd /opt/bj-presale-tracker
python3 -m venv .venv
.venv/bin/pip install -e .
```

如果暂时没有 Git 仓库，也可以先用压缩包上传，但长期建议放进 Git，后续更新会简单很多。

## 5. 设置刷新口令

创建生产环境配置：

```bash
cp .env.example .env
```

生成一个随机口令：

```bash
openssl rand -hex 32
```

编辑 `.env`，把生成的值填进去：

```bash
nano .env
```

示例：

```text
REFRESH_TOKEN=这里换成随机长口令
```

以后管理员在网页上点“刷新”时，浏览器会提示输入这个口令。普通访客不知道口令，就只能查看页面，不能触发抓取。

## 6. 先手动试运行

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

再开一个服务器终端测试：

```bash
curl http://127.0.0.1:8000/api/dashboard
```

能返回 JSON 就说明应用本身跑起来了。

按 `Ctrl+C` 停止手动运行。

## 7. 配置 systemd 常驻运行

复制服务文件：

```bash
cp deploy/bj-presale-tracker.service.example /etc/systemd/system/bj-presale-tracker.service
```

如果项目路径不是 `/opt/bj-presale-tracker`，需要编辑服务文件里的路径：

```bash
nano /etc/systemd/system/bj-presale-tracker.service
```

启动服务：

```bash
systemctl daemon-reload
systemctl enable bj-presale-tracker
systemctl start bj-presale-tracker
systemctl status bj-presale-tracker
```

查看日志：

```bash
journalctl -u bj-presale-tracker -f
```

## 8. 安装并配置 Caddy

安装 Caddy：

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt -o /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install -y caddy
```

编辑 Caddy 配置：

```bash
nano /etc/caddy/Caddyfile
```

把 `example.com` 换成你的域名：

```caddyfile
example.com {
    reverse_proxy 127.0.0.1:8000
}
```

检查并重载：

```bash
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
```

现在访问：

```text
https://你的域名/
```

## 9. 日常更新

以后代码更新后，在服务器执行：

```bash
cd /opt/bj-presale-tracker
git pull
.venv/bin/pip install -e .
systemctl restart bj-presale-tracker
```

## 10. 备份数据

当前数据库默认在：

```text
data/app.db
```

建议定期备份这个文件。最简单的手动备份：

```bash
mkdir -p /opt/backups/bj-presale-tracker
cp /opt/bj-presale-tracker/data/app.db /opt/backups/bj-presale-tracker/app-$(date +%F).db
```

## 11. 排查

网页打不开：

```bash
systemctl status bj-presale-tracker
systemctl status caddy
journalctl -u bj-presale-tracker -n 100
journalctl -u caddy -n 100
```

域名打不开：

- 确认域名 A 记录指向服务器公网 IP
- 确认服务器安全组开放 `80` 和 `443`
- 确认 Caddyfile 里的域名拼写正确
- 如果是大陆服务器，确认备案已通过

刷新失败：

- 确认输入的是 `.env` 里的 `REFRESH_TOKEN`
- 查看应用日志：`journalctl -u bj-presale-tracker -f`
- 确认服务器能访问北京住建委网站
