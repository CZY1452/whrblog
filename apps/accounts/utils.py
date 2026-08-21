import typing
from datetime import timedelta

from django.core.cache import cache
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from core.utils import send_email

_code_ttl = timedelta(minutes=5)


def send_verify_email(to_mail: str, code: str, subject: str = _("Verify Email")):
    """发送重设密码验证码
    Args:
        to_mail: 接受邮箱
        subject: 邮件主题
        code: 验证码
    """
    html_content = _(
        "You are resetting the password, the verification code is：%(code)s, valid within 5 minutes, please keep it "
        "properly") % {'code': code}
    send_email([to_mail], subject, html_content)


def verify(email: str, code: str) -> typing.Optional[str]:
    """验证code是否有效
    Args:
        email: 请求邮箱
        code: 验证码
    Return:
        如果有错误就返回错误str
    Node:
        这里的错误处理不太合理，应该采用raise抛出
        否测调用方也需要对error进行处理
    """
    cache_code = get_code(email)
    if cache_code != code:
        return gettext("Verification code error")


def set_code(email: str, code: str):
    """设置code"""
    cache.set(email, code, _code_ttl.seconds)


def get_code(email: str) -> typing.Optional[str]:
    """获取code"""
    return cache.get(email)


# ===== 注册邮箱验证码（独立缓存键，1 分钟有效期 + 1 分钟限发）=====
# 与忘记密码验证码（_code_ttl=5min，键名为邮箱本身）完全隔离，互不影响。
_reg_code_ttl = timedelta(minutes=1)       # 验证码有效期：1 分钟
_reg_code_cooldown = 60                     # 同一邮箱冷却：1 分钟内只能发 1 个验证码


def set_reg_code(email: str, code: str):
    """存储注册验证码（1 分钟过期）"""
    cache.set(f'reg_verify_code:{email}', code, _reg_code_ttl.seconds)


def get_reg_code(email: str) -> typing.Optional[str]:
    """获取注册验证码"""
    return cache.get(f'reg_verify_code:{email}')


def verify_reg_code(email: str, code: str) -> typing.Optional[str]:
    """校验注册验证码；成功则删除（防重复使用），失败返回错误字符串"""
    cache_code = get_reg_code(email)
    if not cache_code or cache_code != code:
        return gettext('验证码错误或已过期')
    cache.delete(f'reg_verify_code:{email}')
    return None


def reg_code_can_send(email: str) -> bool:
    """是否可发送：受 1 分钟冷却限制，冷却中返回 False"""
    return cache.get(f'reg_verify_cd:{email}') is None


def reg_code_mark_sent(email: str):
    """标记已发送，开启 1 分钟冷却"""
    cache.set(f'reg_verify_cd:{email}', 1, _reg_code_cooldown)


def send_reg_verify_email(to_mail: str, code: str):
    """发送注册验证码邮件（中文，1 分钟内有效）"""
    subject = _('邮箱验证验证码')
    html_content = _(
        '您的注册验证码为：%(code)s，1 分钟内有效，请勿泄露给他人。'
    ) % {'code': code}
    send_email([to_mail], subject, html_content)
