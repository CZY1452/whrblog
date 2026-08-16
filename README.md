<div align="center">

# 📝 WhrBlog

**一个前后端分离的个人博客系统**

基于 Django + Vue3 构建，支持全文搜索、评论互动、容器化一键部署

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-REST%20API-A30000?style=flat-square)](https://www.django-rest-framework.org/)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-9.4-FEC514?style=flat-square&logo=elasticsearch&logoColor=black)](https://www.elastic.co/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## 🛠 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Django 5.2 + Django REST Framework |
| 数据库 | MySQL 8.0 |
| 缓存 / 队列 | Redis 7 + Celery |
| 搜索引擎 | Elasticsearch 9.4 + IK 中文分词 |
| 前端 | Vue3 + Vite + Tailwind CSS + Pinia |
| Web 服务器 | Gunicorn + Nginx |
| 部署 | Docker / Docker Compose |

## 🏗 系统架构

```
浏览器
  │  (80/443)
  ▼
┌─────────────────────────────────────────┐
│  Nginx（反向代理 / 静态托管）            │
│   ├── /api/*、/admin/* ──► backend:8000 │
│   └── 其他 ──► frontend (Vue SPA)       │
└─────────────────────────────────────────┘
        │
        ▼
┌───────────────┐   ┌───────────────┐
│  backend      │   │  worker        │  Celery 异步任务
│  Gunicorn     │──►│  复用后端镜像   │
│  + Django     │   └───────┬───────┘
└──┬────┬───┬───┘           │
   │    │   │               ▼
   │    │   │         ┌───────────┐
   │    │   └────────►│  Redis    │  缓存 + 队列
   │    │             └───────────┘
   │    ▼
   │  ┌───────────┐
   └─►│  MySQL    │  主数据库
      └───────────┘
        │
        ▼
  ┌──────────────┐
  │ Elasticsearch│  全文搜索（IK 分词）
  └──────────────┘
```

## 📁 项目结构

```
whrblog/
├── apps/                  # 业务应用
│   ├── blog/              # 文章、分类、标签、站点设置
│   ├── comments/          # 评论、表情反应
│   ├── accounts/          # 用户、认证
│   └── servermanager/     # 服务器管理（命令备忘、邮件发送日志）
├── core/                  # 通用工具（缓存、ES 客户端、信号、插件系统）
├── plugins/               # 插件系统
├── whrblog/               # 项目配置（settings、urls、celery、wsgi）
├── frontend/              # Vue3 前端源码
├── deploy/                # 部署配置（Dockerfile、nginx、entrypoint）
├── docker-compose.yml     # 容器编排
├── requirements.txt       # 后端依赖
└── manage.py              # Django 管理入口
```

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 20+
- MySQL 8.0 / Redis 7 / Elasticsearch 9.4（可用 Docker 一键启动）
- Docker & Docker Compose（生产部署）

### 方式一：Docker 一键部署（推荐，零配置开箱即用）

```bash
# 1. 复制开发环境变量模板（已含纯 Docker 默认配置，无需修改即可本地运行）
cp .env.example .env

# 2. 构建并启动所有服务
docker compose up -d --build

# 3.（可选）创建管理员；若已导入数据可跳过
docker compose exec backend python manage.py createsuperuser
```

> `.env.example` 中的 MySQL / Redis / Elasticsearch 均指向 Docker 服务名（mysql / redis / elasticsearch），并使用了开发默认密码。克隆到任意机器后执行 `cp .env.example .env && docker compose up -d` 即可直接跑起来，无需本地安装任何数据库或中间件。
> 生产部署请把 `.env` 中的密码、`SECRET_KEY`、邮箱授权码等替换为真实值（可参考 `deploy/.env.prod`）。
>
> ⚠️ **仅限本地开发**：`.env.example` 里的 `DEBUG=True`、`ALLOWED_HOSTS=*` 以及写死的 `SECRET_KEY` 仅供本地开发。生产环境必须改为 `DEBUG=False`、将 `ALLOWED_HOSTS` 限定为真实域名、并生成随机 `SECRET_KEY`，否则存在调试信息泄露与 Host 头攻击风险。
>
> 💡 **预置示例数据**：若想直接拥有 123 篇技术文章与 admin 账号，在 `docker compose up -d` 之后运行 `bash deploy/seed/load_seed.sh`（脚本会导入种子 SQL 并重建 Elasticsearch 索引）。

### 方式二：本地开发

```bash
# 1. 安装后端依赖
pip install -r requirements.txt

# 2. 配置 .env（参考 deploy/.env.prod）并启动后端
python manage.py migrate
python manage.py runserver

# 3. 启动 Celery（Windows 需加 --pool=solo）
celery -A whrblog worker -l info --pool=solo

# 4. 启动前端
cd frontend && npm install && npm run dev
```

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">
  <sub>Built with ❤️ by Whr</sub>
</div>
