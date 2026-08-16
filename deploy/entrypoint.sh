#!/bin/bash
set -e

echo "==> Waiting for MySQL..."
for i in $(seq 1 30); do
    python -c "
import socket
s = socket.socket()
try:
    s.connect(('${DJANGO_MYSQL_HOST:-mysql}', ${DJANGO_MYSQL_PORT:-3306}))
    print('MySQL is ready!')
    exit(0)
except Exception:
    exit(1)
finally:
    s.close()
" 2>/dev/null && break
    echo "  attempt $i/30, retrying in 2s..."
    sleep 2
done

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> Compressing static assets..."
python manage.py compress --force 2>/dev/null || true

echo "==> Initializing Elasticsearch index (best-effort)..."
# 幂等：索引不存在则创建，已存在则复用并全量同步已发布文章；ES 异常时不阻塞后端启动
python manage.py rebuild_es_index --no-delete || \
    echo "  (ES 索引初始化失败，搜索将回退到数据库模糊查询)"

echo "==> Starting Gunicorn..."
exec gunicorn whrblog.wsgi:application \
    --config /app/gunicorn.conf.py
