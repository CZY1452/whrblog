import logging

from django.core import signing as django_signing
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from .models import BlogUser

logger = logging.getLogger(__name__)

# 纯 API 架构：注册/登录/登出/忘记密码/用户中心全部由 accounts.api_views 提供。
# 本文件仅保留邮件链接跳回所需的薄重定向端点。


def change_email_confirm(request, id, sign):
    """改邮箱确认：验证签名与新邮箱后更新用户邮箱，然后跳转 SPA 结果页"""
    new_email = request.GET.get('email')
    if not new_email:
        return HttpResponseForbidden()
    try:
        data = django_signing.loads(
            sign, salt='change-email', max_age=86400)
        if data.get('user_id') != int(id) or data.get('new_email') != new_email:
            raise django_signing.BadSignature
    except django_signing.BadSignature:
        return HttpResponseForbidden()
    user = get_object_or_404(BlogUser, pk=id)
    if BlogUser.objects.filter(email=new_email).exclude(pk=id).exists():
        return HttpResponseRedirect('/user?email=changed-failed')
    user.email = new_email
    user.save(update_fields=['email', 'last_modify_time'])
    return HttpResponseRedirect('/user?email=changed')
