# WhrBlog 全容器化部署指南（部署思路 + 避坑）

> 面向已经跑过 `docker compose up -d --build` 的开发者，把"为什么这么写"讲清楚，
> 覆盖：配置从哪来、各服务密码在哪定义、初始化边界、以及实战踩过的坑。

---

## 一、心智模型：一个部署只回答 6 个问题

`docker-compose.yml` 的本质是为每个服务声明 6 件事：

| 问题 | 对应写法 | 本仓库示例 |
|------|----------|------------|
| 1. 用谁的镜像？ | `image:`（官方）或 `build:`（自建） | mysql/redis/nginx 用官方，backend/frontend/es 自建 |
| 2. 服务间怎么通信？ | 服务名 + `networks:`，不靠 IP/端口 | backend 连 `mysql`、`redis`、`elasticsearch` |
| 3. 数据放哪？ | `volumes:` 命名卷 | mysql_data / redis_data / es_data / static / media |
| 4. 配置差异怎么办？ | `env_file:` + `environment:` + 默认值 | `${VAR:-default}` 双轨 |
| 5. 启动顺序？ | `depends_on:` + `condition: service_healthy` | backend 等 mysql/redis/es healthy |
| 6. 挂了怎么办？ | `restart:` + `healthcheck:` | 全部 `unless-stopped` + 自定义探测 |

---

## 二、三类服务的写法

### A. 官方镜像直接用（mysql / redis / nginx）
不需要自己写 Dockerfile，但要按官方约定的环境变量名声明用户名密码：

```yaml
mysql:
  image: mysql:8.0                  # 固定 tag，别用 latest
  environment:
    MYSQL_DATABASE: ${DJANGO_MYSQL_DATABASE:-whrblog}
    MYSQL_USER: ${DJANGO_MYSQL_USER:-whr}
    MYSQL_PASSWORD: ${DJANGO_MYSQL_PASSWORD:-123456}
    MYSQL_ROOT_PASSWORD: ${DJANGO_MYSQL_PASSWORD:-123456}
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${DJANGO_MYSQL_PASSWORD}"]
    interval: 10s
    retries: 5
    start_period: 30s
```

> 变量名是镜像规定死的：`MYSQL_USER` / `MYSQL_PASSWORD` / `ELASTIC_PASSWORD` / `--requirepass`。
> 换名字会导致脚本认不出、建不出你要的用户。

### B. 自建应用镜像（backend / frontend）
写 Dockerfile + `build:`，并给镜像命名：

```yaml
backend:
  build:
    context: .                      # context 决定把哪些文件发给 Docker 去构建
    dockerfile: Dockerfile
  image: whrblog-backend:latest    # 自建镜像也命名，便于复用缓存
```

### C. 官方镜像壳 + 自定义内容（elasticsearch + IK 插件）
在官方镜像基础上叠一层自己的文件：

```yaml
elasticsearch:
  build:
    context: ./deploy/es            # ⚠️ context 必须指向 Dockerfile 实际依赖文件的目录
    dockerfile: Dockerfile
  environment:
    - ELASTIC_PASSWORD=${ES_PASSWORD:-whr1452}   # ES 9.x 默认开安全认证
```

---

## 三、配置从哪来：一个统一来源，Docker 替你分发

这是"一键启动感觉不到设密码"的原因——本地手动做的事全被镜像启动脚本封装了：

```
.env 文件（你手动创建）
   │  docker compose 读取，${VAR} 从这里取值
   ▼
docker-compose.yml 的 environment 字段
   │  找不到就取 : 后面的默认值
   ▼
容器里的环境变量
   │
   ▼
mysql 启动脚本：看到 MYSQL_USER 就建用户、设密码
redis 启动脚本：--requirepass 启用密码
ES 启动脚本：用 ELASTIC_PASSWORD 设置 elastic 用户密码
backend settings.py：读 DJANGO_MYSQL_* / REDIS_* 连库
```

### 双轨默认值
- 提供 `.env`（由 `.env.example` 或 `.env.prod` 复制而来，已被 .gitignore 忽略）
- compose 里所有敏感变量写 `"${VAR:-default}"`，没 `.env` 也能跑（开发默认值）

### 关键前提：**初始化只在空卷时执行**
官方镜像脚本"建用户"这步**只在数据卷为空（首次启动）时运行**。
卷里已有旧数据 → 跳过建用户 → 改 `.env` 密码也不会生效。

=> 判断链：报"配置不对"先查三处——`.env` 有没有、compose 默认值对不对、数据卷是不是残留旧数据（`down -v` 删卷重来）。

---

## 四、Dockerfile 三条铁律（踩坑总结）

### 1. 网络源决定构建体验
大陆环境 apt/pip/npm 全要换国内源，否则 apt 装依赖能从 32kB/s 卡到"假死"：

```dockerfile
RUN sed -i \
        -e 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        -e 's|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends gcc ...

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

前端 npm 同理：`npm ci --registry=https://registry.npmmirror.com`

### 2. 行尾即命运
`entrypoint.sh` 必须 **LF 行尾**，否则镜像里 `exec /app/entrypoint.sh`
报 `no such file or directory`（CRLF 的 `\r` 混进 shebang `#!/bin/sh\r`）。
用 `.gitattributes` 锁死：
```
*.sh text eol=lf
```

### 3. 缓存层级
先 COPY 依赖清单（requirements.txt / package.json）再装依赖，最后 COPY 源码
→ 以后改代码不会触发重装依赖。

### 4. `.dockerignore` 必须有
防止把 node_modules / .git / .env 塞进 build context 和镜像。

---

## 五、项目名与数据卷隔离（换环境的坑）

**项目名默认取目录名**：`warning: 两个目录都叫 whrblog → 项目名撞车`
项目名决定卷名/网络名/容器名前缀，同名即共库：

- `whrblog_mysql_data` 被两个目录共用
- MySQL 只对空卷初始化 => 新环境挂旧卷 => whr 密码还是旧的 => Access denied

**修复（二选一）**：
1. compose 顶部加 `name: <固定项目名>`，把项目名与目录名解耦（推荐）
2. 或换环境时重命名目录（如 `whrblog-test`），或 `docker compose -p <name>` 隔离

---

## 六、完整执行流（含初始化）

```bash
cp .env.example .env                 # 生产用 cp .env.prod .env
docker compose build                 # 先打镜像；卡住加 --progress=plain
docker compose up -d                 # 再起；多服务开始时 nginx 可能被依赖链暂缓
docker compose ps                    # 检查全部 healthy
docker compose logs -f backend       # 看日志
docker compose exec backend python manage.py createsuperuser   # 首次建账号
```

清干净重来：`docker compose down -v`（⚠️ 删卷，数据丢失）

### 为什么第一个 `up` 后 nginx 是 Created 而不是 Started
`nginx depends_on backend condition: service_healthy`——
如果 backend 首次启动失败(未达 healthy)，nginx 不会被启动。
`backend unhealthy` 的常见原因：数据库密码不匹配 / entrypoint.sh 行尾错误。
修好后 `docker compose up -d` 补齐即可。

---

## 七、本仓库配置速查表：变量从哪来到哪去

| 变量 | 定义位置 | 默认值 | 消费方 |
|------|----------|--------|--------|
| DJANGO_MYSQL_USER | .env / compose | whr | backend.settings + mysql 建用户 |
| DJANGO_MYSQL_PASSWORD | .env / compose | 123456 | backend 连库 + mysql root/whr 密码 |
| DJANGO_MYSQL_DATABASE | .env / compose | whrblog | backend + mysql 建库 |
| DJANGO_SECRET_KEY | .env / compose | 开发默认串（生产必换） | Django 签名 |
| DJANGO_DEBUG | .env / compose | True（生产 False） | Django |
| DJANGO_ALLOWED_HOSTS | .env / compose | *,127.0.0.1,localhost | Django |
| REDIS_PASSWORD | .env / compose | whr1452 | redis --requirepass + backend |
| ES_PASSWORD | .env / compose | whr1452 | ES elastic 用户 + backend |
| DJANGO_EMAIL_* | .env | CHANGE_ME（不影响启动） | 邮件发送 |
| COMPRESS_OFFLINE | .env | False | collectstatic/压缩 |

---

## 八、服务清单

| 服务 | 镜像 | 端口(容器内) | 对外暴露 | 角色 |
|------|------|-------------|----------|------|
| nginx | nginx:1.27-alpine | 80 | ✅ 80 | 唯一入口，反代 API/静态 |
| frontend | whrblog-frontend(自建) | 80 | ❌ | Vue 构建产物 |
| backend | whrblog-backend(自建) | 8000 | ❌ | Django+Gunicorn |
| worker | 同一 backend 镜像 | - | ❌ | Celery 异步任务 |
| mysql | mysql:8.0 | 3306 | ❌ | 主库 |
| redis | redis:7-alpine | 6379 | ❌ | 缓存 + Celery broker |
| elasticsearch | whrblog-es(自建+IK) | 9200/9300 | ❌ | 全文搜索 |