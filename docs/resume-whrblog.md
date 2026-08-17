# WhrBlog 个人博客系统 — 简历模板

## 项目经历

**whrblog 全栈个人博客 ｜ Python / Django / Vue ｜ 2024.03 – 至今**

独立从零设计并实现的前后端分离个人博客平台，容器化一键部署。

**技术栈**：Python 3.12 · Django 5.2 + DRF · MySQL 8.0 · Redis · Celery · Elasticsearch · Vue 3 + Vite · Tailwind CSS · Docker Compose · GitHub Actions

**核心成果**：

- 设计全站 RESTful API（文章/分类/标签/评论/用户），统一分页格式；接口自描述 `page_size`，解除前后端分页硬编码耦合；
- 集成 Elasticsearch 全文搜索（IK 分词，相关性排序 + 高亮），异常自动降级 ORM 模糊查询，保证高可用；
- 基于 Signal + Celery 构建事件旁路：数据变更自动失效 Redis 缓存、异步同步 ES 索引、异步发通知邮件；
- 设计插件化内容管线（the_content 过滤器链）：外链安全化、图片懒加载、版权声明，可插拔互不影响；
- 优化性能：消除分类/评论 N+1 查询；浏览计数按 IP+文章 10 分钟去重，Redis 故障降级；
- pytest **187 项全部通过**；GitHub Actions CI（测试 + 迁移校验 + 前端构建 + 镜像构建）；Docker Compose 编排 7 服务一键部署上线。

## 技能关键词

| 分类 | 关键词 |
|------|--------|
| 后端 | Django 5.2、DRF、RESTful API、Session 认证、Celery、Signal |
| 数据 | MySQL 8.0、Redis 缓存、Elasticsearch（IK 分词） |
| 前端 | Vue 3、Vite、Pinia、Vue Router、Tailwind CSS |
| 可靠性 | N+1 优化、缓存降级、限流、XSS 清洗（bleach）、CSRF 防护 |
| 工程化 | Docker Compose、Nginx、Gunicorn、GitHub Actions、pytest |