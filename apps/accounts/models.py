from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


# 在此定义模型

class BlogUser(AbstractUser):
    nickname = models.CharField(_('昵称'), max_length=100, blank=True)
    avatar = models.CharField(_('头像'), max_length=350, blank=True, default='')
    creation_time = models.DateTimeField(_('创建时间'), default=now)
    last_modify_time = models.DateTimeField(_('修改时间'), default=now)
    source = models.CharField(_('注册来源'), max_length=100, blank=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-id']
        verbose_name = _('用户')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'
