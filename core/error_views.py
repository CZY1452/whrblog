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


def render_error_page(request, status_code, message, exception=None):
    """兼容旧接口签名，统一走 JSON 错误体"""
    return _error_response(request, status_code, message, exception)


def page_not_found_view(request, exception, template_name='blog/error_page.html'):
    return _error_response(
        request,
        404,
        'Sorry, the page you requested is not found.',
        exception
    )


def server_error_view(request, template_name='blog/error_page.html'):
    return _error_response(
        request,
        500,
        'Sorry, the server is busy, please try again later.',
    )


def permission_denied_view(request, exception, template_name='blog/error_page.html'):
    return _error_response(
        request,
        403,
        'Sorry, you do not have permission to access this page.',
        exception
    )


def bad_request_view(request, exception, template_name='blog/error_page.html'):
    return _error_response(
        request,
        400,
        'Sorry, the request was invalid.',
        exception
    )
