基于 `docker-compose.yml` 全文，整理出所有 `${VAR:-default}` 默认值：

## 后端 `backend`（worker 同款）

| 变量 | 默认值 | 用途 |
|---|---|---|
| `DJANGO_MYSQL_USER` | `whr` | 数据库用户名 |
| `DJANGO_MYSQL_PASSWORD` | `123456` | 数据库密码（backend 连库用） |
| `DJANGO_MYSQL_DATABASE` | `whrblog` | 数据库名 |
| `REDIS_PASSWORD` | `whr1452` | Redis 密码（拼进 `DJANGO_REDIS_URL`） |
| `DJANGO_SECRET_KEY` | `django-insecure-dev-only-not-for-prod-whrblog-9f8e7d6c5b4a3210` | Django 安全密钥 |
| `DJANGO_DEBUG` | `True` | 调试模式 |
| `DJANGO_ALLOWED_HOSTS` | `*,127.0.0.1,localhost` | 允许的主机 |
| `ES_PASSWORD` | `whr1452` | ES elastic 用户密码 |

注意：`DJANGO_MYSQL_HOST`、`DJANGO_MYSQL_PORT`、`ES_HOST` 是**写死**的（`mysql`/`3306`/`http://elasticsearch:9200`），没有默认值语法，因为必须走 Docker 服务名。

## MySQL

| 变量 | 默认值 |
|---|---|
| `MYSQL_DATABASE` | `whrblog`（同 `DJANGO_MYSQL_DATABASE`） |
| `MYSQL_USER` | `whr`（同 `DJANGO_MYSQL_USER`） |
| `MYSQL_PASSWORD` | `123456`（同 `DJANGO_MYSQL_PASSWORD`） |
| `MYSQL_ROOT_PASSWORD` | `123456`（**复用同一个密码**） |

> 全部值从 backend 的三个变量取，`.env` 里只需设一遍。

## Redis

| 变量 | 默认值 |
|---|---|
| `REDIS_PASSWORD` | `whr1452`（`--requirepass`） |

## Elasticsearch

| 变量 | 默认值 |
|---|---|
| `ES_PASSWORD` | `whr1452`（`ELASTIC_PASSWORD`） |

## 硬编码值（无默认值语法，固定）

- 所有 `image:`、`container_name:`、`restart: unless-stopped`
- MySQL 启动参数：`utf8mb4` / `utf8mb4_unicode_ci` / buffer pool 256M / max_connections 200
- Redis：`--maxmemory 256mb --maxmemory-policy allkeys-lru`
- ES：`discovery.type=single-node`、`ES_JAVA_OPTS=-Xms512m -Xmx512m`
- 所有健康检查（interval/timeout/retries/start_period）
- 卷、网络、端口映射、挂载路径
