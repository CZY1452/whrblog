#!/usr/bin/env python
# encoding: utf-8

"""
Django Blog 全局常量定义
包含缓存超时时间等配置
"""


# ===== 缓存过期时间（秒）=====
class CacheTimeout:
    """
    缓存超时时间常量
    集中管理所有缓存过期时间，便于统一调整缓存策略
    """
    # 分钟级
    MINUTE_1 = 60
    MINUTE_5 = 60 * 5
    MINUTE_10 = 60 * 10
    MINUTE_30 = 60 * 30

    # 小时级
    HOUR_1 = 60 * 60
    HOUR_2 = 60 * 60 * 2
    HOUR_10 = 60 * 60 * 10
    HOUR_24 = 60 * 60 * 24

    # 天级
    DAY_7 = 60 * 60 * 24 * 7
    DAY_30 = 60 * 60 * 24 * 30

    # 默认缓存时间
    DEFAULT = HOUR_10  # 10小时
