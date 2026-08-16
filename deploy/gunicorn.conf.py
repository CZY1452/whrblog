# Gunicorn 生产配置
# 文档：https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing
import os

# --- 基础配置 ---
bind = "0.0.0.0:8000"
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
# gthread：基于线程的 worker，适合存在 ES 搜索、邮件等 IO 密集/外部依赖的接口。
# 注意：sync worker 下 worker_connections 无效，故改用 gthread + threads。
worker_class = "gthread"
threads = int(os.environ.get('GUNICORN_THREADS', 4))
timeout = 120
graceful_timeout = 30
keepalive = 5

# --- 进程管理 ---
max_requests = 1000          # 工作进程处理 1000 请求后重启（防止内存泄漏）
max_requests_jitter = 50     # 随机偏移，避免所有进程同时重启
preload_app = True           # 预加载应用，减少内存占用

# --- 日志 ---
accesslog = "-"              # 输出到 stdout（Docker 日志收集）
errorlog = "-"
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# --- 安全 ---
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# --- 进程名 ---
proc_name = "whrblog"

# --- 启动后钩子 ---
def on_starting(server):
    """服务启动前"""
    pass

def post_fork(server, worker):
    """worker 进程 fork 后"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """exec 新的二进制前"""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """服务就绪"""
    server.log.info("Server is ready. PID: %s", os.getpid())
