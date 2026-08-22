# ============================================================
#  WhrBlog Elasticsearch 镜像
#  基于官方 ES 9.4.3，额外安装 IK 中文分词插件
#  （官方镜像不含 analysis-ik，会导致创建索引时 analyzer 找不到）
# ============================================================
FROM docker.elastic.co/elasticsearch/elasticsearch:9.4.3

# 安装 IK 中文分词插件（版本必须与 ES 主版本一致）
# 采用离线安装：需先下载 elasticsearch-analysis-ik-9.4.3.zip 放到本目录（与 Dockerfile 同级）
#   下载地址：https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-9.4.3.zip
#   （get.infini.cloud 在线安装已不可用，返回 502）
COPY elasticsearch-analysis-ik-9.4.3.zip /tmp/ik.zip
RUN bin/elasticsearch-plugin install --batch file:///tmp/ik.zip

# 固定 ES 配置：关闭首次启动自动生成的 http.ssl（TLS），改用明文 HTTP + 密码认证，
# 与 backend 的 ES_HOST=http://elasticsearch:9200 对齐。
# 若不固定，新服务器 / 重建镜像时 ES 会自动把 9200 端口改为 HTTPS，导致连接被掐。
COPY elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml
