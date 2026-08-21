from abc import abstractmethod

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from slugify import slugify

from core.utils import cache_decorator
from core.constants import CacheTimeout


class LinkShowType(models.TextChoices):
    I = ('i', _('首页'))
    L = ('l', _('列表'))
    P = ('p', _('文章'))
    A = ('a', _('全站'))
    S = ('s', _('幻灯片'))


class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)
    creation_time = models.DateTimeField(_('创建时间'), default=now)
    last_modify_time = models.DateTimeField(_('修改时间'), default=now)

    def save(self, *args, **kwargs):
        if 'slug' in self.__dict__:
            slug = getattr(
                self, 'title') if 'title' in self.__dict__ else getattr(
                self, 'name')
            setattr(self, 'slug', slugify(slug))
        super().save(*args, **kwargs)

    def get_full_url(self):
        from core.utils import get_site_url
        return f"{get_site_url()}{self.get_absolute_url()}"

    class Meta:
        abstract = True

    @abstractmethod
    def get_absolute_url(self):
        pass


class Article(BaseModel):
    """文章"""
    STATUS_CHOICES = (
        ('d', _('草稿')),
        ('p', _('已发布')),
    )
    COMMENT_STATUS = (
        ('o', _('开放')),
        ('c', _('关闭')),
    )
    TYPE = (
        ('a', _('文章')),
        ('p', _('页面')),
    )
    title = models.CharField(_('标题'), max_length=200, unique=True)
    body = models.TextField(_('正文'))
    pub_time = models.DateTimeField(
        _('发布时间'), blank=False, null=False, default=now)
    status = models.CharField(
        _('状态'),
        max_length=1,
        choices=STATUS_CHOICES,
        default='p')
    comment_status = models.CharField(
        _('评论状态'),
        max_length=1,
        choices=COMMENT_STATUS,
        default='o')
    type = models.CharField(_('类型'), max_length=1, choices=TYPE, default='a')
    views = models.PositiveIntegerField(_('浏览量'), default=0)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('作者'),
        blank=False,
        null=False,
        on_delete=models.CASCADE)
    article_order = models.IntegerField(
        _('排序'), blank=False, null=False, default=0)
    is_top = models.BooleanField(_('置顶'), blank=False, null=False, default=False)
    show_toc = models.BooleanField(_('显示目录'), blank=False, null=False, default=False)
    category = models.ForeignKey(
        'Category',
        verbose_name=_('分类'),
        on_delete=models.CASCADE,
        blank=False,
        null=False)
    tags = models.ManyToManyField('Tag', verbose_name=_('标签'), blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-article_order', '-pub_time']
        verbose_name = _('文章')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'
        indexes = [
            # 优化列表查询：type + status + pub_time组合索引
            models.Index(fields=['type', 'status', '-pub_time'], name='idx_type_status_pub'),
            # 优化热门文章查询：status + views组合索引
            models.Index(fields=['status', '-views'], name='idx_status_views'),
            # 优化作者文章查询：author + status + type组合索引
            models.Index(fields=['author', 'status', 'type'], name='idx_author_status_type'),
            # 优化分类查询：category + status组合索引
            models.Index(fields=['category', 'status'], name='idx_category_status'),
        ]

    def get_absolute_url(self):
        return f"/article/{self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def viewed(self):
        from django.db.models import F
        Article.objects.filter(pk=self.pk).update(views=F('views') + 1)
        self.views = (self.views or 0) + 1

    def get_admin_url(self):
        info = (self._meta.app_label, self._meta.model_name)
        return reverse('admin:%s_%s_change' % info, args=(self.pk,))

    @cache_decorator(expiration=CacheTimeout.HOUR_10)
    def next_article(self):
        # 下一篇
        return Article.objects.filter(
            id__gt=self.id, status='p').order_by('id').first()

    @cache_decorator(expiration=CacheTimeout.HOUR_10)
    def prev_article(self):
        # 前一篇
        return Article.objects.filter(id__lt=self.id, status='p').first()


class Category(BaseModel):
    """文章分类"""
    name = models.CharField(_('分类名称'), max_length=30, unique=True)
    parent_category = models.ForeignKey(
        'self',
        verbose_name=_('父分类'),
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    slug = models.SlugField(_('别名'), default='no-slug', max_length=60, blank=True)
    index = models.IntegerField(default=0, verbose_name=_('排序'))

    class Meta:
        ordering = ['-index']
        verbose_name = _('分类')
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return f"/category/{self.slug}"

    def __str__(self):
        return self.name


class Tag(BaseModel):
    """文章标签"""
    name = models.CharField(_('标签名称'), max_length=30, unique=True)
    slug = models.SlugField(_('别名'), default='no-slug', max_length=60, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/tag/{self.slug}"

    @cache_decorator(CacheTimeout.HOUR_10)
    def get_article_count(self):
        return Article.objects.filter(tags__name=self.name).distinct().count()

    class Meta:
        ordering = ['name']
        verbose_name = _('标签')
        verbose_name_plural = verbose_name


class Links(models.Model):
    """友情链接"""

    name = models.CharField(_('链接名称'), max_length=30, unique=True)
    link = models.URLField(_('链接'))
    sequence = models.IntegerField(_('排序'), unique=True)
    is_enable = models.BooleanField(
        _('是否显示'), default=True, blank=False, null=False)
    show_type = models.CharField(
        _('显示位置'),
        max_length=1,
        choices=LinkShowType.choices,
        default=LinkShowType.I)
    creation_time = models.DateTimeField(_('创建时间'), default=now)
    last_mod_time = models.DateTimeField(_('修改时间'), default=now)

    class Meta:
        ordering = ['sequence']
        verbose_name = _('友情链接')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SideBar(models.Model):
    """侧边栏,可以展示一些html内容"""
    name = models.CharField(_('标题'), max_length=100)
    content = models.TextField(_('内容'))
    sequence = models.IntegerField(_('排序'), unique=True)
    is_enable = models.BooleanField(_('是否启用'), default=True)
    creation_time = models.DateTimeField(_('创建时间'), default=now)
    last_mod_time = models.DateTimeField(_('修改时间'), default=now)

    class Meta:
        ordering = ['sequence']
        verbose_name = _('侧边栏')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class BlogSettings(models.Model):
    """blog的配置"""

    COLOR_SCHEMES = (
        ('purple', _('紫色主题 - Purple Dream')),
        ('blue', _('蓝色主题 - Ocean Blue')),
        ('green', _('绿色主题 - Forest Green')),
        ('orange', _('橙色主题 - Sunset Orange')),
        ('pink', _('粉色主题 - Cherry Blossom')),
        ('red', _('红色主题 - Ruby Red')),
        ('indigo', _('靛蓝主题 - Midnight Indigo')),
        ('teal', _('青色主题 - Teal Wave')),
    )

    site_name = models.CharField(
        _('网站名称'),
        max_length=200,
        null=False,
        blank=False,
        default='')
    site_description = models.TextField(
        _('网站描述'),
        max_length=1000,
        null=False,
        blank=False,
        default='')
    site_seo_description = models.TextField(
        _('网站SEO描述'), max_length=1000, null=False, blank=False, default='')
    site_keywords = models.TextField(
        _('网站关键词'),
        max_length=1000,
        null=False,
        blank=False,
        default='')
    article_sub_length = models.IntegerField(_('文章摘要长度'), default=300)
    sidebar_article_count = models.IntegerField(_('侧边栏文章数'), default=10)
    sidebar_comment_count = models.IntegerField(_('侧边栏评论数'), default=5)
    article_comment_count = models.IntegerField(_('文章评论数'), default=5)
    show_google_adsense = models.BooleanField(_('显示广告'), default=False)
    google_adsense_codes = models.TextField(
        _('广告代码'), max_length=2000, null=True, blank=True, default='')
    open_site_comment = models.BooleanField(_('开启站点评论'), default=True)
    color_scheme = models.CharField(
        _('配色方案'),
        max_length=20,
        choices=COLOR_SCHEMES,
        default='purple',
        help_text=_('选择网站的主题配色方案'))
    global_header = models.TextField("公共头部", null=True, blank=True, default='')
    global_footer = models.TextField("公共尾部", null=True, blank=True, default='')
    beian_code = models.CharField(
        '备案号',
        max_length=2000,
        null=True,
        blank=True,
        default='')
    analytics_code = models.TextField(
        "网站统计代码",
        max_length=1000,
        null=False,
        blank=False,
        default='')
    show_gongan_code = models.BooleanField(
        '是否显示公安备案号', default=False, null=False)
    gongan_beiancode = models.TextField(
        '公安备案号',
        max_length=2000,
        null=True,
        blank=True,
        default='')
    comment_need_review = models.BooleanField(
        '评论是否需要审核', default=False, null=False)

    class Meta:
        verbose_name = _('网站配置')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.site_name

    def clean(self):
        if BlogSettings.objects.exclude(id=self.id).count():
            raise ValidationError(_('There can only be one configuration'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from core.utils import cache
        cache.clear()
