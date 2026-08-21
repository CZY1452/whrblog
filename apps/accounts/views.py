from django.core import signing as django_signing
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from .models import BlogUser

# 纯 API 架构：注册/登录/登出/忘记密码/用户中心全部由 accounts.api_views 提供。
# 本文件仅保留邮件链接跳回所需的薄端点（change_email / verify_email）。


def verify_email_confirm(request):
    """注册邮箱激活（验证码方式）：渲染自包含验证码输入页，无需前端 SPA 接管。

    作为「直连 Django（如邮件客户端打开链接）」的兜底：读取 ?id=，提供 6 位码
    输入框，提交时调用 /api/verify_email（与 SPA 同一后端接口）。生产环境由
    nginx 把 /verify-email 交给 SPA 处理，此视图仅作本地/无前端兜底。
    """
    user_id = request.GET.get('id') or ''
    html = (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>邮箱验证</title></head>'
        '<body style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;'
        'max-width:480px;margin:80px auto;padding:0 16px;text-align:center;color:#333">'
        '<h1 style="font-size:22px">邮箱验证</h1>'
        '<p style="color:#666;line-height:1.6">请前往您的邮箱查收 6 位验证码'
        '（1 分钟内有效），输入后即完成账号激活。</p>'
        '<form id="vf" onsubmit="return doVerify(event)">'
        '<input id="code" name="code" inputmode="numeric" autocomplete="one-time-code" '
        'maxlength="6" required placeholder="6 位验证码" '
        'style="width:220px;padding:12px;font-size:20px;text-align:center;'
        'border:1px solid #ccc;border-radius:8px;letter-spacing:6px">'
        '<input type="hidden" id="uid" value="{uid}">'
        '<p style="margin-top:18px"><button type="submit" '
        'style="padding:10px 30px;border:0;border-radius:8px;background:#2563eb;'
        'color:#fff;font-size:15px;cursor:pointer">验证</button></p>'
        '</form>'
        '<p id="msg" style="margin-top:18px;min-height:22px;font-size:15px"></p>'
        '<script>'
        'function doVerify(e){e.preventDefault();'
        'var code=document.getElementById("code").value.trim();'
        'var uid=document.getElementById("uid").value;'
        'if(!uid){document.getElementById("msg").textContent="缺少用户参数";'
        'document.getElementById("msg").style.color="#dc2626";return false;}'
        'document.getElementById("msg").textContent="验证中…";'
        'document.getElementById("msg").style.color="#666";'
        'fetch("/api/verify_email",{method:"POST",'
        'headers:{"Content-Type":"application/json"},'
        'body:JSON.stringify({id:uid,code:code})})'
        '.then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})'
        '.then(function(res){var d=res.data;'
        'document.getElementById("msg").textContent=d.message||d.error||"验证失败";'
        'document.getElementById("msg").style.color=d.success?"#16a34a":"#dc2626";});'
        'return false;}'
        '</script>'
        '</body></html>'
    ).format(uid=user_id)
    return HttpResponse(html)


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
