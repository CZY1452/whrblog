# ============================================================
#  WhrBlog Docker 后端镜像
#  Python 3.12 + Django 5.2 + Gunicorn
# ============================================================
FROM python:3.12-slim

# 系统依赖（mysqlclient 编译需要）
RUN sed -i \
        -e 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        -e 's|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        libjpeg-dev \
        libpng-dev \
        libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制项目代码
COPY . /app/
# 复制部署脚本和配置
COPY deploy/entrypoint.sh /app/entrypoint.sh
COPY deploy/gunicorn.conf.py /app/gunicorn.conf.py
RUN chmod +x /app/entrypoint.sh

# 创建必要的目录（日志已统一输出 stdout，不再写 logs 文件目录）
RUN mkdir -p /app/uploads /app/collectedstatic

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
