# 部署到远程服务器

以下步骤假设：

- 服务器系统是 Ubuntu
- 项目部署目录是 `/opt/yijing-web`
- 域名是 `your-domain.com`

## 1. 域名解析

在你的域名 DNS 管理后台添加：

- `A` 记录：`@` 指向你的服务器公网 IP
- `A` 记录：`www` 指向你的服务器公网 IP

## 2. 服务器安装基础环境

```bash
sudo apt update
sudo apt install -y python3 python3-venv nginx certbot python3-certbot-nginx
```

## 3. 上传项目

把整个项目上传到服务器：

```bash
sudo mkdir -p /opt/yijing-web
sudo chown -R $USER:$USER /opt/yijing-web
```

然后把本地项目文件传到服务器，例如：

```bash
scp -r ./ root@your-server-ip:/opt/yijing-web
```

如果你不是 root，请改成你的服务器用户名。

## 4. 安装 Python 依赖

```bash
cd /opt/yijing-web
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 5. 配置 systemd 服务

先编辑服务文件中的以下值：

- `User`
- `WorkingDirectory`
- `ExecStart`
- `LLM_API_KEY`

把 [deploy/yijing-web.service](/E:/chowey/deploy/yijing-web.service:1) 复制到服务器：

```bash
sudo cp deploy/yijing-web.service /etc/systemd/system/yijing-web.service
sudo systemctl daemon-reload
sudo systemctl enable yijing-web
sudo systemctl start yijing-web
sudo systemctl status yijing-web
```

## 6. 配置 Nginx

编辑 [deploy/nginx-yijing.conf](/E:/chowey/deploy/nginx-yijing.conf:1) 中的域名：

- `your-domain.com`
- `www.your-domain.com`

然后部署：

```bash
sudo cp deploy/nginx-yijing.conf /etc/nginx/sites-available/yijing-web
sudo ln -s /etc/nginx/sites-available/yijing-web /etc/nginx/sites-enabled/yijing-web
sudo nginx -t
sudo systemctl reload nginx
```

## 7. 申请 HTTPS 证书

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

成功后访问：

- `https://your-domain.com`
- `https://www.your-domain.com`

## 8. 常用排查命令

查看应用日志：

```bash
sudo journalctl -u yijing-web -f
```

查看 nginx 日志：

```bash
sudo tail -f /var/log/nginx/error.log
```

检查后端健康状态：

```bash
curl http://127.0.0.1:8000/health
```

## 9. 更新代码后重启

```bash
cd /opt/yijing-web
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart yijing-web
```
