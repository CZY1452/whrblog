"""DRF 自定义分页。

在标准分页响应基础上补充 `page` 与 `page_size` 字段，
让前端从接口响应中读取分页参数，避免前端硬编码每页条数与后端
DRF_PAGE_SIZE 隐式耦合。
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PageSizePagination(PageNumberPagination):
    """每页条数可由客户端通过 `page_size` 查询参数覆盖，上限受 max_page_size 限制。"""
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
