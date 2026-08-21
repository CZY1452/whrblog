#!/usr/bin/env python
# encoding: utf-8

"""
Django Blog 统一错误处理视图

纯 API 架构下统一返回 JSON 错误体，供 SPA 前端展示。
"""

import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _error_response(request, status_code, message, exception=None):
    if exception:
        logger.error(
            f'HTTP {status_code} Error: {exception}',
            exc_info=True,
            extra={
                'request': request,
                'status_code': status_code
            }
        )
    return JsonResponse(
        {
            'error': message,
            'status_code': status_code,
        },
        status=status_code,
    )


def page_not_found_view(request, exception, template_name='blog/error_page.html'):
    return _error_response(
        request,
        404,
        '抱歉，您请求的页面未找到。',
        exception
    )


def server_error_view(request, template_name='blog/error_page.html'):
    return _error_response(
        request,
        500,
        '抱歉，服务器繁忙，请稍后重试。',
    )


def permission_denied_view(request, exception, template_name='blog/error_page.html'):
    return _error_response(
        request,
        403,
        '抱歉，您没有访问此页面的权限。',
        exception
    )
