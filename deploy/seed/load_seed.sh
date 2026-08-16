#!/usr/bin/env bash
# ============================================================
#  WhrBlog 数据库种子加载脚本
#  作用：将仓库内置的示例数据（123 篇技术文章 + admin 账号等）
#        导入到 docker compose 启动的 MySQL 中，并重建 ES 索引。
#  前提：已执行 `docker compose up -d` 且 MySQL 容器健康。
#  用法：bash deploy/seed/load_seed.sh
#  注意：脚本会 DROP 并重建 whrblog 库中的相关表（仅开发/演示用）。
# ============================================================
set -euo pipefail

# 切到项目根目录（本脚本位于 deploy/seed/）
cd "$(dirname "$0")/../.."

# 读取 .env 中的连接信息（若存在），否则使用内置开发默认值
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

DB_NAME="${DJANGO_MYSQL_DATABASE:-whrblog}"
DB_USER="${DJANGO_MYSQL_USER:-whr}"
DB_PASS="${DJANGO_MYSQL_PASSWORD:-123456}"
SEED_FILE="deploy/seed/whrblog_seed.sql"

if [ ! -f "$SEED_FILE" ]; then
  echo "❌ 未找到种子文件: $SEED_FILE"
  exit 1
fi

echo "==> 等待 MySQL 健康 ..."
for i in $(seq 1 30); do
  if docker compose exec -T mysql mysqladmin ping -h localhost -u root -p"$DB_PASS" --silent >/dev/null 2>&1; then
    echo "  MySQL 已就绪"
    break
  fi
  echo "  attempt $i/30, 等待 2s ..."
  sleep 2
done

echo "==> 导入种子数据: $SEED_FILE"
docker compose exec -T mysql \
  mysql -uroot -p"$DB_PASS" --default-character-set=utf8mb4 "$DB_NAME" < "$SEED_FILE"

echo "==> 重建 Elasticsearch 索引（best-effort）..."
docker compose exec -T backend python manage.py rebuild_es_index --no-delete \
  || echo "  (ES 索引重建失败，搜索将回退到数据库查询，不影响站点运行)"

echo "✅ 种子数据加载完成。"
echo "   前台: http://127.0.0.1/   后台: http://127.0.0.1/admin/   (账号 admin / whrblog1)"
