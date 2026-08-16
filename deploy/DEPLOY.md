## WhrBlog 部署指南（Docker Compose）

本文档覆盖从零到上线的完整流程。项目采用 Docker Compose 编排，包含 Django 后端、Vue 前端、Nginx 反向代理、MySQL、Redis、Elasticsearch 六个服务。

---

### 一、服务器要求

推荐配置：2 核 CPU / 4GB 内存 / 40GB SSD 以上。Elasticsearch 较吃内存，JVM 默认分配 512MB，加上 MySQL、Redis、Django，4GB 是最低线。如果预算允许，8GB 会更从容。

操作系统推荐 Ubuntu 22.04 / 24.04 LTS 或 Debian 12。

### 二、服务器初始化

SSH 登录服务器后，安装 Docker 和 Docker Compose：

```bash
# 安装 Docker（官方一键脚本）
curl -fsSL https://get.docker.com | sh

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
# 重新登录使生效

# 验证
docker --version
docker compose version
```

安装 Git 并拉取代码：

```bash
cd /opt
git clone <你的仓库地址> whrblog
cd whrblog
```

### 三、域名与 DNS

在你的域名注册商（阿里云、Cloudflare 等）添加两条 A 记录，都指向服务器 IP：

```
yourdomain.com     → 服务器 IP
www.yourdomain.com → 服务器 IP
```

### 四、配置环境变量

```bash
# 复制生产环境模板
cp deploy/.env.prod .env

# 编辑 .env，修改所有 CHANGE_ME 占位符
nano .env
```

必须修改的项：

| 变量 | 说明 |
|------|------|
| `DJANGO_SECRET_KEY` | 用 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` 生成 |
| `DJANGO_ALLOWED_HOSTS` | 改为你的域名，如 `yourdomain.com,www.yourdomain.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | 改为 `https://yourdomain.com,https://www.yourdomain.com` |
| `DJANGO_MYSQL_PASSWORD` | 设置强密码 |
| `REDIS_PASSWORD` | 设置强密码，同时更新 `DJANGO_REDIS_URL` 中的密码部分 |
| `ES_PASSWORD` | 设置 ES 密码 |
| `DJANGO_EMAIL_*` | 配置你的发件邮箱 |
| `DJANGO_SECURE_SSL` | 启用 HTTPS 后保持 `True` |

### 五、修改 Nginx 配置中的域名

编辑 `deploy/nginx/conf.d/default.conf`，将所有 `yourdomain.com` 替换为你的实际域名：

```bash
sed -i 's/yourdomain.com/你的实际域名/g' deploy/nginx/conf.d/default.conf
```

### 六、首次启动

```bash
# 构建并启动所有服务
docker compose up -d --build

# 查看启动状态
docker compose ps

# 查看后端日志（确认迁移和 collectstatic 成功）
docker compose logs -f backend
```

首次启动时 backend 会自动执行数据库迁移和 collectstatic。等待所有服务健康检查通过后，用 IP 直接访问 `http://服务器IP` 应该能看到前端页面。

### 七、创建管理员账号

```bash
docker compose exec backend python manage.py createsuperuser
```

### 八、初始化 Elasticsearch 索引（已自动化）

后端启动脚本（`entrypoint.sh`）会自动创建 ES 索引并同步已发布文章（幂等，重复执行安全）。
如遇索引异常需手动重建，可执行：

```bash
docker compose exec backend python manage.py rebuild_es_index
```

### 九、配置 HTTPS（Let's Encrypt）

**第一步：先用 HTTP 获取证书**

确保 Nginx 配置中 HTTPS server 段保持注释状态（默认就是注释的），启动服务后执行：

```bash
# 安装 certbot
sudo apt install certbot

# 获取证书（Nginx 需要在运行中）
sudo certbot certonly --webroot -w /var/www/certbot \
    -d yourdomain.com -d www.yourdomain.com \
    --docker-volume whrblog_certbot_conf
```

或者更简单的方式——直接在服务器上用 standalone 模式：

```bash
# 先停 Nginx 释放 80 端口
docker compose stop nginx

# 用 certbot standalone 获取证书
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 将证书复制到 Docker volume
sudo docker run --rm \
    -v /etc/letsencrypt:/source:ro \
    -v whrblog_certbot_conf:/target \
    alpine cp -r /source/. /target/

# 重启 Nginx
docker compose start nginx
```

**第二步：启用 HTTPS 配置**

编辑 `deploy/nginx/conf.d/default.conf`：

1. 取消 HTTPS server 段（`listen 443 ssl`）的注释
2. 取消 HTTP→HTTPS 重定向段的注释
3. 将其中所有 `yourdomain.com` 替换为实际域名
4. 将证书路径改为实际路径

```bash
# 重载 Nginx 配置
docker compose exec nginx nginx -s reload
```

**第三步：更新 Django 配置**

确保 `.env` 中 `DJANGO_SECURE_SSL=True`，然后重启后端：

```bash
docker compose restart backend
```

**第四步：配置证书自动续期**

在 docker-compose.yml 中取消 certbot 服务的注释，然后：

```bash
docker compose up -d certbot
```

### 十、日常运维命令

```bash
# 查看所有服务状态
docker compose ps

# 查看实时日志
docker compose logs -f              # 所有服务
docker compose logs -f backend      # 仅后端

# 重启某个服务
docker compose restart backend

# 重新构建并部署（代码更新后）
git pull
docker compose up -d --build backend
docker compose up -d --build frontend

# 进入后端容器执行管理命令
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py rebuild_es_index    # 重建 ES 索引

# 数据库备份
docker compose exec mysql mysqldump -uwhr -p whrblog > backup_$(date +%Y%m%d).sql

# 数据库恢复
docker compose exec -T mysql mysql -uwhr -p whrblog < backup_20250101.sql

# 清理 Docker 无用资源（谨慎）
docker system prune -f
```

### 十一、文件结构说明

部署相关文件在项目中的位置：

```
whrblog/
├── Dockerfile                    # 后端镜像（Python + Django + Gunicorn）
├── Dockerfile.frontend           # 前端镜像（Node 构建 → Nginx 托管）
├── docker-compose.yml            # 服务编排（6 个服务）
├── .dockerignore                 # Docker 构建忽略文件
├── deploy/
│   ├── .env.prod                 # 生产环境变量模板
│   ├── entrypoint.sh             # 后端启动脚本（等待 DB → 迁移 → 启动）
│   ├── gunicorn.conf.py          # Gunicorn 配置（worker 数、超时等）
│   └── nginx/
│       ├── nginx.conf            # Nginx 主配置（gzip、安全 headers）
│       └── conf.d/
│           └── default.conf      # 站点配置（反代 + 静态资源 + SPA）
```

### 十二、架构概览

```
浏览器
  │
  ▼
Nginx (:80/:443)
  ├── /api/*  ──────→  backend:8000 (Gunicorn + Django)
  ├── /admin/*  ────→  backend:8000
  ├── /static/*  ───→  collectedstatic/ (本地文件, 30天缓存)
  ├── /media/*  ────→  uploads/ (本地文件, 7天缓存)
  └── /*  ──────────→  frontend (Vue SPA, index.html)
                           │
                     backend:8000 (API)
                       ├── MySQL 8.0 (:3306)
                       ├── Redis 7 (:6379)
                       └── Elasticsearch 9 (:9200)
```

### 十三、常见问题

**Q: 后端启动失败，日志显示 "MySQL not ready"**
entrypoint.sh 会自动等待最多 60 秒。如果 MySQL 启动较慢，可以手动重启：`docker compose restart backend`。

**Q: 前端页面 404**
确认 frontend 容器已构建成功：`docker compose logs frontend`。如果 dist 为空，重新构建：`docker compose up -d --build frontend`。

**Q: 搜索功能不可用**
确认 ES 容器健康：`docker compose logs elasticsearch`。首次使用需建立索引：`docker compose exec backend python manage.py rebuild_es_index`。

**Q: 头像上传失败**
检查 uploads volume 权限：`docker compose exec backend ls -la /app/uploads`。

**Q: 如何查看 Django 报错**
```bash
# 日志已统一输出到 stdout，直接通过 docker compose logs 查看
docker compose logs --tail=100 backend
docker compose logs -f backend
```
