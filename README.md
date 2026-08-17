<div align="center">

# 📝 WhrBlog

**一个前后端分离的个人博客系统**

基于 Django 5.2 + Vue3 构建，内置全文搜索、评论审核、插件系统与容器化一键部署

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-A30000?style=flat-square)](https://www.django-rest-framework.org/)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-9.4-FEC514?style=flat-square&logo=elasticsearch&logoColor=black)](https://www.elastic.co/)
[![pytest](https://img.shields.io/badge/pytest-187%20passed-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## ✨ 功能特性

- **文章系统**：Markdown 写作 / 草稿箱 / 页面类型 / Markdown 渲染前置 XSS 清洗；支持阅读量统计（单 IP 去重）、上一篇/下一篇导航、文章目录（TOC）
- **归档与检索**：分类（支持多级）、标签、作者归档；Elasticsearch 全文搜索（IK 中文分词），ES 不可用时自动回退到 ORM 模糊查询
- **评论互动**：评论 / 回复 / 表情反应，管理员审核后展示，新评论邮件通知
- **用户体系**：注册（邮箱验证）、登录（记住我）、找回密码、修改密码 / 邮箱 / 头像
- **SEO 内建**：sitemap.xml、文章摘要、每页独立的 SEO 标题 / 描述 / 关键词
- **插件系统**：内置 外部链接处理、图片懒加载、文章版权声明 三个插件；`hooks` 过滤器机制（文章正文渲染后管线）
- **工程化**：全站 DRF 接口自描述分页参数、侧边栏聚合接口、站点信息接口、深色模式、Django Admin 后台
- **可靠性**：Redis 缓存读写异常 graceful 降级；BlogSettings 缓存信号自动失效

## 🛠 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Django 5.2 + Django REST Framework 3.15 |
| 数据库 | MySQL 8.0 |
| 缓存 / 队列 | Redis 7 + Celery 5.6（ES 同步、邮件发送） |
| 搜索引擎 | Elasticsearch 9.4 + IK 中文分词 |
| 前端 | Vue 3 + Vite 6 + Tailwind CSS + Pinia + Vue Router |
| Web 服务器 | Gunicorn + Nginx |
| 测试 | pytest + pytest-django（187 项测试） |
| 部署 | Docker / Docker Compose |

## 🏗 系统架构

```
浏览器
  │  (80)
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
│   ├── blog/              # 文章、分类、标签、站点设置、搜索、上传/导入导出
│   ├── comments/          # 评论、回复、表情反应
│   ├── accounts/          # 用户、注册登录、邮箱验证、账号中心
│   └── servermanager/     # 服务器命令备忘、邮件发送日志
├── core/                  # 通用能力（缓存、ES 客户端、插件管理、信号、分页、sitemap）
├── plugins/               # 内置内容过滤器插件
│   ├── external_links/      # 外部链接处理
│   ├── image_lazy_loading/  # 图片懒加载
│   └── article_copyright/   # 文章版权声明
├── whrblog/               # 项目配置（settings、urls、celery、wsgi、管理命令）
├── frontend/              # Vue3 前端源码（src/router、src/views、src/stores）
├── deploy/                # 部署（Dockerfile、nginx、entrypoint、seed、生产 env 模板）
├── docker-compose.yml     # 容器编排（7 个服务）
├── Dockerfile             # 后端镜像
├── Dockerfile.frontend    # 前端多阶段构建镜像
├── pytest.ini             # pytest 配置
├── requirements.txt       # 后端依赖
└── manage.py              # Django 管理入口
```

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose v2（推荐，一条命令启动全部依赖）
- 本地开发另需：Python 3.12+、Node.js 20+

### 方式一：Docker 一键部署（推荐）

```bash
# 1. 复制环境变量模板（内置纯 Docker 开发默认值，无需修改即可跑起来）
cp .env.example .env
# cp .env.prod .env（私人生产环境没有进行上传）

# 2. 构建并启动全部 7 个服务（MySQL/Redis/ES/后端/前端/Nginx/Worker）
docker compose up -d --build

# 3.（可选）创建管理员账号
docker compose exec backend python manage.py createsuperuser
```

启动完成后访问：

| 入口 | 地址 |
|------|------|
| 前台首页（Vue SPA） | http://localhost |
| Django Admin 后台 | http://localhost/admin/ |
| 健康检查 | http://localhost/health |

> 💡 **预置示例数据**：若想直接拥有 123 篇技术文章与 admin 账号，运行 `bash deploy/seed/load_seed.sh`（导入种子 SQL 并重建 Elasticsearch 索引）。
>
> ⚠️ **仅限本地开发**：`.env.example` 中的 `DEBUG=True`、`ALLOWED_HOSTS=*`、写死的 `SECRET_KEY` 仅供开发环境。生产部署请参考 [deploy/DEPLOY.md](deploy/DEPLOY.md)。

### 方式二：本地开发

```bash
# 1. 安装后端依赖
pip install -r requirements.txt

# 2. 配置 .env（参考 .env.prod）并启动迁移与后端
python manage.py migrate
python manage.py runserver

# 3. 启动 Celery Worker（Windows 需加 --pool=solo）
celery -A whrblog worker -l info --pool=solo

# 4. 启动前端 Vite 开发服务器
cd frontend && npm install && npm run dev
```

## 🧪 测试

```bash
# Docker 环境（推荐）：容器内直接跑全部 187 项测试
docker compose exec -T backend pytest

# 本地（需可用的 MySQL/Redis 环境）
pytest
```

全量测试覆盖 core、accounts、blog、comments、servermanager 五个模块，含插件系统、公开 API、权限、草稿、导入导出、评论工作流等。

## 🔌 API 概览

纯 REST API 架构，返回统一分页结构（`count / page / page_size / next / previous / results`）。

| 模块 | 端点 |
|------|------|
| 文章 | `GET/POST /api/articles/`（支持 `category` / `tag` / `author` 过滤） |
| 文章详情 / 草稿 | `GET /api/articles/<id>/`、`/api/drafts/` |
| 分类 / 标签 | `GET /api/categories/`、`GET /api/tags/`（含子分类树、SEO 字段） |
| 搜索 | `GET /api/search/?q=` |
| 评论 | `GET /api/comments/?article=`、发评论 / 回复 / 表情 |
| 侧边栏聚合 | `GET /api/sidebar/?linktype=` |
| 站点信息 | `GET /api/siteinfo/`（导航分类、标签、页面） |
| 用户 | `/api/register` `/api/login` `/api/logout` `/api/user` `/api/verify_email` `/api/forget_password` `/api/change_password` `/api/change_email` `/api/upload_avatar` |
| 内容管理 | `/api/article_create` `/api/upload` `/api/clean_cache` `/api/articles/import/` `/api/articles/<id>/export/` |
| 站点地图 / 健康 | `/sitemap.xml` `/health/` |

## 🔧 常用运维命令

```bash
docker compose ps                                  # 查看所有服务状态
docker compose logs -f backend                     # 查看后端日志
docker compose exec backend bash                   # 进入后端容器排障
docker compose exec backend python manage.py check --deploy   # Django 生产检查
docker compose exec backend python manage.py rebuild_es_index  # 重建 ES 索引
docker compose exec backend python manage.py clear_cache       # 清理缓存
docker compose down                                # 停止全部
docker compose up -d --build                       # 重新构建并启动
```

## 📦 部署

生产环境部署（纯 HTTP、IP 直访、无需域名/证书）请参见完整的 **[部署指南 → deploy/DEPLOY.md](deploy/DEPLOY.md)**。

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">
  <sub>Built with ❤️ by Whr</sub>
</div>