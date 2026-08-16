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

### 方式一：Docker 一键部署（推荐）

```bash
# 1. 复制环境变量模板并填写
cp deploy/.env.prod .env

# 2. 构建并启动所有服务
docker compose up -d --build

# 3. 创建管理员
docker compose exec backend python manage.py createsuperuser
```

> 首次构建会自动完成数据库迁移、静态文件收集、ES 索引初始化，访问 `http://localhost` 即可。

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
