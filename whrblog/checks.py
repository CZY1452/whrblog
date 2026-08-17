"""生产安全守卫（Django system check）。

目标：消除"零配置启动用了开发默认值（DEBUG=True / ALLOWED_HOSTS=* / 写死 SECRET_KEY）
会在不知不觉中被用于生产"的陷阱。

- DEBUG=True 且 ALLOWED_HOSTS 含 '*'：发出 WARNING（这是开发配置，严禁上生产）。
- 生产（DEBUG=False）却仍使用明显的开发默认 SECRET_KEY：发出 ERROR（部署会失败，倒逼修改）。
"""
from django.conf import settings
from django.core.checks import Error, Warning, register


@register()
def check_insecure_development_config(app_configs, **kwargs):
    errors = []

    allowed = settings.ALLOWED_HOSTS or []
    if settings.DEBUG and "*" in allowed:
        errors.append(Warning(
            "DEBUG=True 且 ALLOWED_HOSTS 包含 '*' —— 这是开发配置，严禁用于生产环境。",
            hint="生产部署请使用 .env.prod 模板，显式设置 "
                 "DJANGO_DEBUG=False 与具体公网 IP（纯 HTTP 直访，无需域名，"
                 "对应 DJANGO_ALLOWED_HOSTS）。",
            id="whrblog.W001",
        ))

    dev_key_markers = ("django-insecure", "dev-only", "change_me", "changeme", "not-for-prod")
    secret_key = settings.SECRET_KEY or ""
    if not settings.DEBUG and any(m in secret_key.lower() for m in dev_key_markers):
        errors.append(Error(
            "生产环境（DEBUG=False）却使用了明显的开发默认 SECRET_KEY。",
            hint="请通过 DJANGO_SECRET_KEY 设置高强度随机密钥："
                 "python -c \"from django.core.management.utils import get_random_secret_key; "
                 "print(get_random_secret_key())\"",
            id="whrblog.E001",
        ))

    return errors
