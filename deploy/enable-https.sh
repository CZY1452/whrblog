#!/usr/bin/env bash
# ============================================================
#  WhrBlog 启用 HTTPS
#  前置条件：
#    1. 域名（whr.hopto.org）已 A 记录指向本机公网 IP，且 80 端口可从公网访问
#    2. docker compose up -d 已启动（certbot 容器已运行并尝试签发证书）
#    3. 证书已签发：docker compose exec certbot ls /etc/letsencrypt/live/whr.hopto.org
#  用法（在项目根目录执行）：
#    bash deploy/enable-https.sh
# ============================================================
set -e

echo "==> 在 nginx 容器内激活 HTTPS 配置 ..."
docker compose exec -T nginx sh -c '
  if [ ! -f /etc/letsencrypt/live/whr.hopto.org/fullchain.pem ]; then
    echo "错误：未找到证书 /etc/letsencrypt/live/whr.hopto.org/fullchain.pem"
    echo "请先确认 certbot 已成功签发（docker compose logs certbot）。"
    exit 1
  fi
  cp /etc/nginx/https.conf.template /etc/nginx/conf.d/https.conf
  nginx -t
  nginx -s reload
'
echo "✅ HTTPS 已启用，访问 https://whr.hopto.org"
