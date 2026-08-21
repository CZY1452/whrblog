from django.core import signing as django_signing
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from .models import BlogUser

# 纯 API 架构：注册/登录/登出/忘记密码/用户中心全部由 accounts.api_views 提供。
# 本文件仅保留邮件链接跳回所需的薄端点（change_email / verify_email）。


def _verify_result(ok, message):
    """渲染一个自包含的邮箱验证结果页（不依赖前端 SPA）。"""
    title = '邮箱验证成功' if ok else '邮箱验证失败'
    html = (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>{title}</title></head>'
        '<body style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;'
        'max-width:480px;margin:80px auto;padding:0 16px;text-align:center;color:#333">'
        '<h1 style="font-size:22px">{title}</h1>'
        '<p style="color:#666;line-height:1.6">{msg}</p>'
        '</body></html>'
    ).format(title=title, msg=message)
    return HttpResponse(html, status=200 if ok else 400)


def verify_email_confirm(request):
    """注册邮箱激活：邮件链接直达，无需前端 SPA 接管。

    与 change_email_confirm 一致，提供服务端兜底，避免本地直连 Django 时
    /verify-email 路由 404（该路由原本只由前端 SPA 接管后调用 api/verify_email）。
    """
    user_id = request.GET.get('id')
    sign = request.GET.get('sign')
    if not user_id or not sign:
        return HttpResponseForbidden('参数缺失')
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return HttpResponseForbidden('参数无效')

    user = BlogUser.objects.filter(pk=user_id).first()
    if not user:
        return _verify_result(False, '用户不存在')
    if user.is_active:
        return _verify_result(True, '账号已激活')
    try:
        data = django_signing.loads(sign, salt='email-verify', max_age=86400)
        if data.get('user_id') != user.id:
            raise django_signing.BadSignature
    except django_signing.BadSignature:
        return _verify_result(False, '验证链接无效或已过期')
    user.is_active = True
    user.save(update_fields=['is_active', 'last_modify_time'])
    return _verify_result(True, '邮箱验证成功，账号已激活')


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
