import typing

from django.core.cache import cache
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from core.utils import send_email

# ===== 统一邮箱验证码逻辑（注册 / 密码重置 / 修改邮箱共用）=====
# 每个场景（purpose）使用独立缓存键，互不干扰：
#   verify_code:{purpose}:{email}       验证码本体（1 分钟有效）
#   verify_code_cd:{purpose}:{email}    发送冷却标记（1 分钟内仅可发 1 条）
VERIFY_CODE_TTL = 60
VERIFY_CODE_COOLDOWN = 60

VERIFY_PURPOSES = {
    'register': _('注册'),
    'reset': _('密码重置'),
    'change_email': _('修改绑定邮箱'),
}


def _code_key(email: str, purpose: str) -> str:
    return f'verify_code:{purpose}:{email}'


def _cd_key(email: str, purpose: str) -> str:
    return f'verify_code_cd:{purpose}:{email}'


def set_verify_code(email: str, code: str, purpose: str):
    """存储验证码（1 分钟过期）"""
    cache.set(_code_key(email, purpose), code, VERIFY_CODE_TTL)


def get_verify_code(email: str, purpose: str) -> typing.Optional[str]:
    """获取验证码"""
    return cache.get(_code_key(email, purpose))


def verify_code(email: str, purpose: str, code: str) -> typing.Optional[str]:
    """校验验证码；成功则删除（防重复使用），失败返回错误字符串"""
    cache_code = get_verify_code(email, purpose)
    if not cache_code or cache_code != code:
        return gettext('验证码错误或已过期')
    cache.delete(_code_key(email, purpose))
    return None


def code_can_send(email: str, purpose: str) -> bool:
    """是否可发送：受 1 分钟冷却限制，冷却中返回 False"""
    return cache.get(_cd_key(email, purpose)) is None


def code_mark_sent(email: str, purpose: str):
    """标记已发送，开启 1 分钟冷却"""
    cache.set(_cd_key(email, purpose), 1, VERIFY_CODE_COOLDOWN)


def send_code_email(to_mail: str, code: str, purpose: str):
    """按场景发送中文验证码邮件（注册 / 密码重置 / 修改邮箱）"""
    scene = VERIFY_PURPOSES.get(purpose, _('邮箱验证'))
    subject = _('邮箱验证验证码')
    html_content = _(
        '您正在%(scene)s，验证码为：%(code)s，1 分钟内有效，请勿泄露给他人。'
    ) % {'scene': scene, 'code': code}
    send_email([to_mail], subject, html_content)
