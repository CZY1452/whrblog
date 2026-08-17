# WhrBlog 生产部署指南（纯 HTTP，IP 直访，无需域名 / 证书）

> 本指南面向「一台带公网 IP 的服务器 + 纯 HTTP 访问」场景。
> 不配置 HTTPS、不需要域名、不需要 ICP 备案，开箱即用。
> 若日后需要 HTTPS，再在 Nginx 前加一层证书反代即可；本仓库已移除所有证书签发相关脚手架。

## 一、服务器要求

- 一台可访问公网的 Linux 服务器（本仓库已在 47.113.150.22 验证）
- 已安装 Docker 与 Docker Compose v2
- 入站安全组放通 TCP 80（本指南仅用 80）
- 服务器公网 IP（下文记为 YOUR_SERVER_IP，示例为 47.113.150.22）

## 二、初始化项目

    git clone <your-repo-url> whrblog
    cd whrblog

## 三、准备生产环境变量

    cp deploy/.env.prod .env

然后编辑 .env，至少修改以下【必改】项：

| 变量 | 说明 |
|------|------|
| DJANGO_SECRET_KEY | 用下方命令生成随机串 |
| DJANGO_MYSQL_PASSWORD | MySQL 密码（compose 会据此创建 whr 用户） |
| REDIS_PASSWORD | Redis 密码 |
| ES_PASSWORD | Elasticsearch elastic 用户密码 |
| DJANGO_ALLOWED_HOSTS | 改为 YOUR_SERVER_IP,127.0.0.1,localhost |
| DJANGO_CSRF_TRUSTED_ORIGINS | 改为 http://YOUR_SERVER_IP |
| DJANGO_EMAIL_* | 邮件发送用的 SMTP 账号 / 授权码 |

生成随机 SECRET_KEY：

    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

> 注意：DJANGO_SECURE_SSL 必须保持 False。
> 设为 True 会把 SESSION / CSRF Cookie 标记为 Secure，纯 HTTP 下浏览器不会携带，导致登录与表单全部失败。

## 四、访问方式（IP 直访，无需域名）

部署完成后，直接浏览器访问：

    http://YOUR_SERVER_IP

- 前台首页：http://YOUR_SERVER_IP/
- 后台管理：http://YOUR_SERVER_IP/admin/
- API 根：http://YOUR_SERVER_IP/api/
- 健康检查：http://YOUR_SERVER_IP/health

Nginx 使用 server_name _; 通配，任何指向本机 IP 的请求都会被正确处理，无需配置域名解析。

## 五、首次启动

    docker compose up -d --build

查看状态：

    docker compose ps
    docker compose logs -f backend

## 六、创建管理员

    docker compose exec backend python manage.py createsuperuser

## 七、重建 Elasticsearch 索引

    docker compose exec backend python manage.py search_index --rebuild -f

（可选）预置示例数据：

    bash deploy/seed/load_seed.sh

## 八、常用运维命令

| 操作 | 命令 |
|------|------|
| 查看所有服务状态 | docker compose ps |
| 查看某服务日志 | docker compose logs -f backend |
| 停止全部 | docker compose down |
| 重新构建并启动 | docker compose up -d --build |
| 进入后端容器排障 | docker compose exec backend bash |
| Django 生产检查 | docker compose exec backend python manage.py check --deploy |

## 九、目录结构（部署相关）

    whrblog/
    ├── docker-compose.yml          # 编排（已移除证书签发 / 443 相关配置）
    ├── deploy/
    │   ├── nginx/
    │   │   ├── nginx.conf          # Nginx 主配置（HTTP）
    │   │   └── conf.d/
    │   │       └── default.conf    # 站点配置（server_name _，纯 HTTP）
    │   ├── .env.prod               # 生产环境变量模板（本指南使用）
    │   ├── gunicorn.conf.py        # Gunicorn 配置
    │   ├── entrypoint.sh           # 容器启动入口（collectstatic + 迁移 + 种子）
    │   ├── es/                     # ES 镜像构建（含 IK 分词）
    │   └── seed/                   # 示例数据导入脚本
    └── ...

## 十、服务架构

    浏览器 ──http://YOUR_SERVER_IP:80──► Nginx
                                          ├── /api/*、/admin/* ──► backend:8000 (Django+Gunicorn)
                                          ├── /static/、/media/ ──► 卷挂载
                                          └── 其他 ──► frontend (Vue SPA)
    backend ──► MySQL / Redis / Elasticsearch
    worker  ──► 复用后端镜像，处理邮件与 ES 同步（Celery）

共 7 个服务：backend、worker、frontend、nginx、mysql、redis、elasticsearch。
