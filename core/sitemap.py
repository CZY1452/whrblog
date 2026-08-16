from django.contrib.sitemaps import Sitemap

from apps.blog.models import Article, Category, Tag


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['/', ]

    def location(self, item):
        return item


class ArticleSiteMap(Sitemap):
    changefreq = "monthly"
    priority = "0.6"

    def items(self):
        return Article.objects.filter(status='p')

    def lastmod(self, obj):
        return obj.last_modify_time

    def location(self, obj):
        return f"/article/{obj.id}"


class CategorySiteMap(Sitemap):
    changefreq = "weekly"
    priority = "0.6"

    def items(self):
        return Category.objects.all()

    def lastmod(self, obj):
        return obj.last_modify_time

    def location(self, obj):
        return f"/category/{obj.slug}"


class TagSiteMap(Sitemap):
    changefreq = "weekly"
    priority = "0.3"

    def items(self):
        return Tag.objects.all()

    def lastmod(self, obj):
        return obj.last_modify_time

    def location(self, obj):
        return f"/tag/{obj.slug}"


class UserSiteMap(Sitemap):
    changefreq = "weekly"
    priority = "0.3"

    def items(self):
        from apps.accounts.models import BlogUser
        return list(BlogUser.objects.filter(
            pk__in=Article.objects.filter(status='p').values('author').distinct()
        ))

    def lastmod(self, obj):
        return obj.date_joined

    def location(self, obj):
        return f"/author/{obj.username}"
