"""
Django settings for whrblog project.

由 Django 1.10.2 的 'django-admin startproject' 命令生成。

本文件的更多说明请参见：
https://docs.djangoproject.com/en/1.10/topics/settings/

完整的设置列表及取值请参见：
https://docs.djangoproject.com/en/1.10/ref/settings/
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

# 加载 .env 环境变量文件（项目根目录）
load_dotenv()


def env_to_bool(env, default):
    """将环境变量字符串转换为布尔值，未设置时返回默认值（大小写不敏感）"""
    str_val = os.environ.get(env)
    if str_val is None:
        return default
    return str_val.strip().lower() in ('true', '1', 'yes', 'on')


def env_to_list(env, default):
    """将逗号分隔的环境变量字符串转换为列表，未设置时返回默认列表"""
    str_val = os.environ.get(env)
    if str_val is None:
        return default
    return [item.strip() for item in str_val.split(',') if item.strip()]


def env_to_int(env, default):
    """将环境变量字符串转换为整数，未设置或无效时返回默认值"""
    str_val = os.environ.get(env)
    if str_val is None:
        return default
    try:
        return int(str_val)
    except ValueError:
        return default


# 像这样构建项目内部路径：BASE_DIR / 'subdir'。
BASE_DIR = Path(__file__).resolve().parent.parent

# 开发快速启动设置 - 不适用于生产环境
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# ==================== 核心安全配置 ====================
# 安全警告：请务必在生产环境中保管好 SECRET_KEY 密钥！
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY 环境变量未设置。'
        '请在 .env 文件中设置一个安全的随机密钥。'
    )
# 安全警告：生产环境请勿开启 DEBUG 调试模式！
DEBUG = env_to_bool('DJANGO_DEBUG', False)
TESTING = (len(sys.argv) > 1 and sys.argv[1] == 'test') or 'pytest' in sys.modules

# 允许访问的主机名列表（逗号分隔）
# 开发模式下默认允许本地访问，生产环境必须通过环境变量显式配置
ALLOWED_HOSTS = env_to_list(
    'DJANGO_ALLOWED_HOSTS', ['127.0.0.1', 'localhost'] if DEBUG else [])
# django 4.0新增配置：CSRF 信任的来源域名列表（逗号分隔）
# 注意：纯 API + SPA 架构下，开发态前端由 Vite(5173) 提供，需一并信任。
CSRF_TRUSTED_ORIGINS = env_to_list(
    'DJANGO_CSRF_TRUSTED_ORIGINS', [
        'http://127.0.0.1', 'http://localhost',
        'http://127.0.0.1:5173', 'http://localhost:5173',
    ])

# ==================== 生产安全配置 ====================
# 纯 HTTP 直访部署：本站点不做 HTTPS，故不启用安全 Cookie / HSTS 等。
# 若未来在反向代理层启用 HTTPS，请在此恢复 SESSION_COOKIE_SECURE / CSRF_COOKIE_SECURE 等设置。

# 应用定义


INSTALLED_APPS = [
    # 'django.contrib.admin',
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    'rest_framework',
    'apps.blog.apps.BlogConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.comments.apps.CommentsConfig',
    'apps.servermanager.apps.ServermanagerConfig',
    'compressor',
    'whrblog',
]

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
]

ROOT_URLCONF = 'whrblog.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'whrblog.wsgi.application'

# ==================== 数据库配置 ====================
# 数据库配置说明：https://docs.djangoproject.com/en/1.10/ref/settings/#databases
# 安全警告：生产环境请务必通过环境变量配置数据库账号密码，不要使用默认值！

_db_password = os.environ.get('DJANGO_MYSQL_PASSWORD')
if not _db_password and not DEBUG:
    raise ImproperlyConfigured(
        'DJANGO_MYSQL_PASSWORD 环境变量未设置。'
        '请在 .env 文件中配置数据库密码。'
    )

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DJANGO_MYSQL_DATABASE') or 'whrblog',
        'USER': os.environ.get('DJANGO_MYSQL_USER') or 'root',
        'PASSWORD': _db_password or '',
        'HOST': os.environ.get('DJANGO_MYSQL_HOST') or '127.0.0.1',
        'PORT': int(
            os.environ.get('DJANGO_MYSQL_PORT') or 3306),
        'OPTIONS': {
            'charset': 'utf8mb4'},
    }}

# 密码校验
# 密码校验器说明：https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==================== 国际化和时区 ====================

# 纯 API 架构：语言固定为简体中文（可通过 DJANGO_LANGUAGE_CODE 覆盖）
LANGUAGE_CODE = os.environ.get('DJANGO_LANGUAGE_CODE', 'zh-Hans')

# 时区设置（.env 中可配置）
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'Asia/Shanghai')

# 启用 i18n 以加载 Django 内置中文翻译（admin 界面等）；SPA 前端语言不受影响
USE_I18N = True

# 是否使用带时区的时间（强烈建议开启，与 .env.prod 中 DJANGO_USE_TZ=True 保持一致）
USE_TZ = env_to_bool('DJANGO_USE_TZ', True)

# ==================== 会话配置 ====================
# 会话配置
SESSION_COOKIE_AGE = env_to_int('SESSION_COOKIE_AGE', 1209600)  # 2周（Django默认值）
REMEMBER_ME_LOGIN_TTL = env_to_int('REMEMBER_ME_LOGIN_TTL', 2626560)  # 30天（勾选"记住我"时使用）

# 静态文件（CSS、JavaScript、图片）
# 静态文件说明：https://docs.djangoproject.com/en/1.10/howto/static-files/


# 允许用户使用用户名和密码登录
AUTHENTICATION_BACKENDS = [
    'apps.accounts.user_login_backend.EmailOrUsernameModelBackend']

# ==================== 静态文件配置 ====================
STATIC_ROOT = os.path.join(BASE_DIR, 'collectedstatic')

STATIC_URL = '/static/'

# 静态文件搜索目录（插件静态目录；根目录 static 已随图床上传改存 media 而弃用）
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'plugins'),  # 让Django能找到插件的静态文件
]

AUTH_USER_MODEL = 'accounts.BlogUser'
LOGIN_URL = '/login/'

# ==================== DRF 配置 ====================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.PageSizePagination',
    'PAGE_SIZE': env_to_int('DRF_PAGE_SIZE', 10),
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/min',
        'user': '1000/min',
    },
}

# ==================== 缓存配置 ====================
# 仅使用 Redis 作为缓存后端
_redis_url = os.environ.get('DJANGO_REDIS_URL')
if not _redis_url:
    _redis_host = os.environ.get('REDIS_HOST', '127.0.0.1')
    _redis_port = os.environ.get('REDIS_PORT', '6379')
    _redis_db = os.environ.get('REDIS_DB', '0')
    _redis_pass = os.environ.get('REDIS_PASSWORD', '')
    _redis_auth = f':{_redis_pass}@' if _redis_pass else ''
    _redis_url = f'{_redis_auth}{_redis_host}:{_redis_port}/{_redis_db}'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{_redis_url}',
    }
}

# ==================== Celery 配置 ====================
# Broker 与结果后端复用 Redis（默认使用独立 DB 隔离，1/2 号库）
# 显式配置了 DJANGO_REDIS_URL 时无法拆分，直接复用该连接串（不含 scheme，与 CACHES 一致）
if os.environ.get('DJANGO_REDIS_URL'):
    _celery_broker_url = f'redis://{_redis_url}'
    _celery_result_url = f'redis://{_redis_url}'
else:
    _celery_broker_url = f'redis://{_redis_auth}{_redis_host}:{_redis_port}/1'
    _celery_result_url = f'redis://{_redis_auth}{_redis_host}:{_redis_port}/2'

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', _celery_broker_url)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', _celery_result_url)
CELERY_TIMEZONE = TIME_ZONE
# 测试环境强制 eager（同步执行，不外发任务）；生产需手动启动 worker
CELERY_TASK_ALWAYS_EAGER = env_to_bool('CELERY_TASK_ALWAYS_EAGER', TESTING)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
# core 不在 INSTALLED_APPS 中，autodiscover 扫不到，需显式声明
CELERY_IMPORTS = ('core.tasks',)

SITE_ID = env_to_int('SITE_ID', 1)

# ==================== Elasticsearch 配置 ====================
_es_password = os.environ.get('ES_PASSWORD')
if not _es_password and not DEBUG:
    raise ImproperlyConfigured(
        'ES_PASSWORD 环境变量未设置。'
        '请在 .env 文件中配置 Elasticsearch 密码。'
    )
ELASTICSEARCH_DSL = {
    'hosts': os.environ.get('ES_HOST', 'http://localhost:9200'),
    'basic_auth': (
        os.environ.get('ES_USER', 'elastic'),
        _es_password or '',
    ),
    'verify_certs': env_to_bool('ES_VERIFY_CERTS', False),
    'ssl_show_warn': False,
}
ELASTICSEARCH_INDEX = os.environ.get('ES_INDEX', 'whrblog')

# ==================== 邮箱配置 ====================
# 邮箱：
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = env_to_bool('DJANGO_EMAIL_TLS', False)
EMAIL_USE_SSL = env_to_bool('DJANGO_EMAIL_SSL', True)
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST') or 'smtp.mxhichina.com'
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT') or 465)
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
# 注意：关闭调试模式后，除邮件通知外其他异常均不自动处理
# 管理员邮箱通过 DJANGO_ADMIN_EMAIL 配置；未配置时为空（不发送错误邮件）
_admin_email = os.environ.get('DJANGO_ADMIN_EMAIL')
ADMINS = [('admin', _admin_email)] if _admin_email else []

# ==================== 日志配置 ====================
# 统一输出到 stdout，便于 Docker（docker logs）与本地终端收集；
# gunicorn 的 accesslog/errorlog 也已配置为 stdout，日志链路一致。
_LOGGING_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': _LOGGING_LEVEL,
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d %(module)s] %(message)s',
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': _LOGGING_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'null': {
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'whrblog': {
            'handlers': ['console'],
            'level': _LOGGING_LEVEL,
            'propagate': True,
        }
    }
}

# ==================== 静态资源压缩配置 ====================
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 其他
    'compressor.finders.CompressorFinder',
)
# 开发模式下禁用压缩，使用Vite处理静态资源
COMPRESS_ENABLED = not DEBUG
# 根据环境变量决定是否启用离线压缩
COMPRESS_OFFLINE = os.environ.get('COMPRESS_OFFLINE', 'False').lower() == 'true'

# 压缩输出目录
COMPRESS_OUTPUT_DIR = 'compressed'

# 压缩文件名模板 - 包含哈希值用于缓存破坏
COMPRESS_CSS_HASHING_METHOD = 'mtime'
COMPRESS_JS_HASHING_METHOD = 'mtime'

# 高级CSS压缩过滤器
COMPRESS_CSS_FILTERS = [
    # 创建绝对URL
    'compressor.filters.css_default.CssAbsoluteFilter',
    # CSS压缩器 - 高压缩等级
    'compressor.filters.cssmin.rCSSMinFilter',
]

# 高级JS压缩过滤器
COMPRESS_JS_FILTERS = [
    # JS压缩器 - 高压缩等级
    'compressor.filters.jsmin.rJSMinFilter',
]

# 压缩缓存配置
COMPRESS_CACHE_BACKEND = 'default'
COMPRESS_CACHE_KEY_FUNCTION = 'compressor.cache.simple_cachekey'

# 压缩性能优化
COMPRESS_MINT_DELAY = 30  # 压缩延迟（秒）
COMPRESS_MTIME_DELAY = 10  # 修改时间检查延迟
COMPRESS_REBUILD_TIMEOUT = 2592000  # 重建超时（30天）

# 压缩等级配置
COMPRESS_CSS_COMPRESSOR = 'compressor.css.CssCompressor'
COMPRESS_JS_COMPRESSOR = 'compressor.js.JsCompressor'

# 静态文件缓存配置
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# 浏览器缓存配置（通过中间件或服务器配置）
COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT

# ==================== 媒体文件配置 ====================
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/media/'
X_FRAME_OPTIONS = 'SAMEORIGIN'



# ==================== 其他配置 ====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 插件系统
PLUGINS_DIR = BASE_DIR / 'plugins'
ACTIVE_PLUGINS = [
    'article_copyright',
    'external_links',
    'image_lazy_loading',
]

# ==================== 生产安全守卫 ====================
# 显式导入，确保 whrblog.W001 / whrblog.E001 两个 system check 必定被注册
# （Django 对部分项目级 app 的 checks 模块不会自动发现，此处兜底）。
import whrblog.checks  # noqa: E402,F401