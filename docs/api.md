# WhrBlog API 接口文档

> 适用版本：WhrBlog（Django 5.2 + DRF + Vue3 SPA）
> 文档按 app（模块）分类：`accounts`（账号）、`blog`（博客内容）、`comments`（评论）、`system`（系统级）。

---

## 一、通用约定

### 1.1 基础地址

| 环境 | Base URL |
|------|----------|
| 本地开发（Vite 代理） | `http://localhost:5173`（`/api`、`/media`、`/admin` 等由 Vite 代理到 Django `127.0.0.1:8000`） |
| 本地直连 Django | `http://127.0.0.1:8000` |
| 生产环境 | `https://<你的域名>`（Nginx 同域反代） |

所有接口路径统一以 `/api/` 开头（除健康检查、sitemap、admin、静态资源）。

### 1.2 认证方式（Session 认证）

- 全站使用 **SessionAuthentication**（非 JWT / Token）。
- **登录**：`POST /api/login` 成功后，服务端写入 `sessionid`（HttpOnly Cookie）与 `logged_user`（HttpOnly，标记已登录），后续请求自动携带。
- **登出**：`POST /api/logout` 清除会话与 Cookie。
- **CSRF**：所有写操作（POST / PATCH / PUT / DELETE）需携带 CSRF Token —— 请求头 `X-CSRFToken`（取值自 `csrftoken` Cookie）。前端 `api.js` 已封装自动附加。
- **未登录保护**：匿名访问需登录的接口返回 `401`，前端自动跳转 `/login?next=<当前路径>`。

### 1.3 权限模型

| 权限 | 说明 |
|------|------|
| `AllowAny` | 无需登录（注册、登录、验证码、公开读接口） |
| `IsAuthenticatedOrReadOnly`（DRF 全局默认） | 读操作公开，写操作需登录 |
| `IsAuthenticated` | 必须登录 |
| `IsAdminUser` | 仅管理员（`is_superuser`） |

### 1.4 分页

列表接口使用自定义分页 `PageSizePagination`（`core/pagination.py`），响应包一层分页信封：

```json
{
  "count": 128,          // 总条数
  "page": 1,             // 当前页码（从 1 开始）
  "page_size": 10,       // 实际生效的每页条数
  "next": "http://.../?page=2&page_size=10",
  "previous": null,
  "results": [ ... ]     // 数据数组
}
```

- 查询参数：`page`（页码）、`page_size`（每页条数，默认 `DRF_PAGE_SIZE`，**上限 100**）。
- 注意：`/api/search/` 使用独立分页结构（见 3.5）；`/api/settings/`、`/api/sidebar/`、`/api/siteinfo/` 非列表，不适用分页信封。

### 1.5 限流（Throttle）

| 作用域 | 速率 | 适用接口 |
|--------|------|----------|
| `anon`（全局） | 100/min | 所有匿名请求 |
| `user`（全局） | 1000/min | 所有登录请求 |
| `email` | 3/hour / IP | 重发注册码、改邮箱发信、忘记密码发码 |
| `register_code` | 20/hour / IP | 注册页「发送验证码」 |
| `password_reset` | 10/hour / IP | 忘记密码重置提交 |

超过限流返回 `429`，DRF 原文如 `请求超过了限速。 Expected available in 2774 seconds.`（前端已统一转换为「请求过于频繁，请稍后约 X 分钟再试」，可从 `Retry-After` 头解析等待秒数）。另有「**每邮箱 1 分钟冷却**」的验证码发送兜底（见 2.2）。

### 1.6 错误与状态码约定

- 业务校验失败：`400`，响应体 `{"error": "错误信息"}`（部分接口为 DRF 字段错误 `{"field": ["..."]}`）。
- 未找到：`404`，`{"detail": "..."}` 或 `{"error": "..."}`。
- 未认证：`401`；无权限：`403`；限流：`429`。
- 成功写操作一般返回 `{"success": true, ...}`，新建资源返回 `201`。

---

## 二、accounts —— 账号模块

### 2.1 注册 `POST /api/register`

> 单页内联注册：先发验证码（2.2），再携带 `code` 注册，校验通过即激活，可直接登录。

**权限**：公开（AllowAny）

**请求体**（JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | 是 | 用户名，唯一 |
| `email` | string | 是 | 邮箱，唯一 |
| `nickname` | string | 否 | 昵称 |
| `password` | string | 是 | 密码，≥8 位 |
| `password_confirm` | string | 是 | 确认密码，须与 password 一致 |
| `code` | string | 是 | 邮箱收到的 6 位验证码（1 分钟有效，校验后即失效） |

**响应** `201`：

```json
{ "success": true, "message": "注册成功，邮箱已验证，请登录" }
```

**错误**：`400` 用户名/邮箱已存在、两次密码不一致、验证码错误或过期（`{"error": "..."}`）。

### 2.2 发送注册验证码 `POST /api/send_register_code`

**权限**：公开；**限流**：`register_code` 20/hour/IP + **每邮箱 1 分钟冷却**

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | string | 是 | 注册邮箱（须未注册） |

**响应** `200`：`{"success": true, "message": "验证码已发送，请查收邮箱（1 分钟内有效）"}`

**错误**：`400` 邮箱格式错误 / 该邮箱已注册；`429` 发送过于频繁（冷却期内，`{"error": "验证码发送过于频繁，请 1 分钟后再试"}`）。

### 2.3 登录 `POST /api/login`

**权限**：公开

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | 是 | 用户名 |
| `password` | string | 是 | 密码 |
| `remember` | boolean | 否 | 记住我（默认 false；true 时会话延长为 `REMEMBER_ME_LOGIN_TTL`） |

**响应** `200`：

```json
{
  "success": true,
  "user": {
    "id": 1, "username": "whr", "nickname": "", "avatar": "/media/avatar/1.png",
    "email": "whr@example.com", "is_superuser": true, "date_joined": "2026-01-01T00:00:00+08:00"
  }
}
```

同时下发 Cookie：`sessionid`（HttpOnly）、`logged_user=true`（HttpOnly，SameSite=Lax）。

**错误**：`400` 用户名或密码错误 / 账号未激活。

### 2.4 登出 `POST /api/logout`

**权限**：需登录

**响应** `200`：`{"success": true}`；清除 `sessionid` 与 `logged_user` Cookie。

### 2.5 当前用户信息 `GET /api/user` / 更新昵称 `PATCH /api/user`

**权限**：需登录

- `GET`：返回当前用户（字段同 2.3 的 `user`）。
- `PATCH`：请求体 `{"nickname": "新昵称"}`，返回更新后的用户对象。

### 2.6 邮箱激活验证 `POST /api/verify_email`

> 兜底接口（SPA `/verify-email` 页面调用）：对「已注册未激活」账号用验证码激活。

**权限**：公开

**请求体**：`{"id": 8, "code": "123456"}`

**响应** `200`：`{"success": true, "message": "邮箱验证成功，账号已激活"}`（已激活则提示"账号已激活"）

**错误**：`400` 参数缺失 / 验证码错误或过期；`404` 用户不存在。

### 2.7 重发注册验证码 `POST /api/resend_verify_email`

**权限**：公开；**限流**：`email` 3/hour/IP + 每邮箱 1 分钟冷却

**请求体**：`{"id": 8}`（未激活用户的 id）

**响应** `200`：`{"success": true, "message": "验证码已重新发送"}`

**错误**：`404` 用户不存在或已激活；`429` 发送过于频繁。

### 2.8 忘记密码-发送验证码 `POST /api/forget_password_code`

**权限**：公开；**限流**：`email` 3/hour/IP

**请求体**：`{"email": "xxx@example.com"}`（须已注册，否则 `400 该邮箱未注册`）

**响应** `200`：`{"success": true, "message": "验证码已发送"}`

### 2.9 忘记密码-重置 `POST /api/forget_password`

**权限**：公开；**限流**：`password_reset` 10/hour/IP

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | string | 是 | 注册邮箱 |
| `code` | string | 是 | 邮箱验证码 |
| `new_password` | string | 是 | 新密码 ≥8 位 |
| `new_password_confirm` | string | 是 | 确认新密码 |

**响应** `200`：`{"success": true, "message": "密码重置成功"}`

**错误**：`400` 验证码错误 / 两次密码不一致；`404` 邮箱未注册。

### 2.10 修改密码 `POST /api/change_password`

**权限**：需登录

**请求体**：`{"old_password": "旧密码", "new_password": "新密码≥8位"}`

**响应** `200`：`{"success": true, "message": "密码修改成功"}`

**错误**：`400` 原密码错误。

### 2.11 修改邮箱 `POST /api/change_email`

**权限**：需登录；**限流**：`email` 3/hour/IP

**请求体**：`{"new_email": "新邮箱"}`（须未被占用，否则 `400 该邮箱已被使用`）

**响应** `200`：`{"success": true, "message": "验证邮件已发送至新邮箱，请查收后点击链接确认"}`

> 邮件内含确认链接 `/change_email/<id>/<sign>.html?email=...`，点击后由服务端确认（HTML 兜底页），随后跳转 SPA。

### 2.12 上传头像 `POST /api/upload_avatar`

**权限**：需登录；**格式**：`multipart/form-data`

**请求体**：`avatar` 文件字段。

**限制**：≤2MB；仅 `jpg/jpeg/png/gif/webp`；服务端用 Pillow 重新转码（quality=85）剥离恶意内容；文件名 `uuid.hex` 随机生成。

**响应** `200`：

```json
{ "success": true, "avatar": "/media/avatar/<uuid>.png" }
```

**错误**：`400` 未选择文件 / 过大 / 格式不支持 / 图片无效。

### 2.13 邮件兜底页面（非 JSON API）

| 路径 | 说明 |
|------|------|
| `GET /verify-email` | 注册验证码激活兜底页（HTML 表单，提交到 2.6） |
| `GET /change_email/<id>/<sign>.html` | 改邮箱确认页，点击后生效并跳转 SPA |

---

## 三、blog —— 博客内容模块

### 3.1 文章列表 `GET /api/articles/`

**权限**：公开读。仅返回 **已发布（status=p）、类型为文章（type=a）** 的记录。

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `category` | string | 按分类 slug 筛选 |
| `tag` | string | 按标签 slug 筛选 |
| `author` | string | 按作者用户名筛选 |
| `page` / `page_size` | int | 分页（见 1.4） |

**排序**：全站列表 `-is_top, -article_order, -pub_time`（置顶优先）；分类/标签/作者列表保持默认排序。

**响应**（分页信封，`results` 元素字段）：

```json
{
  "id": 497,
  "title": "基础与缩进",
  "url": "/article/497",
  "summary": "纯文本摘要（按 site 设置截断，默认 300 字）...",
  "type": "a",
  "status": "p",
  "views": 1024,
  "is_top": false,
  "pub_time": "2026-08-01T10:00:00+08:00",
  "creation_time": "2026-08-01T09:59:00+08:00",
  "author": { "id": 2, "username": "whr", "nickname": "", "email": "whr@example.com" },
  "category": { "id": 5, "name": "Python", "slug": "python", "parent_category": null,
                "article_count": 40, "url": "/category/python",
                "seo_title": "...", "seo_description": "...", "child_categories": [] },
  "tags": [ { "id": 1, "name": "python", "slug": "python", "article_count": 30,
              "url": "/tag/python", "seo_title": "...", "seo_description": "..." } ]
}
```

### 3.2 文章详情 `GET /api/articles/<id>/`

**权限**：公开读。访问时**浏览量 +1**（同一 IP 对同一文章 10 分钟内只计一次，Redis 缓存；Redis 不可用时直接计数）。

**响应**：在列表字段基础上增加：

| 字段 | 说明 |
|------|------|
| `body` | 正文 **HTML**（Markdown 渲染 → XSS 清洗 → 插件过滤：外部链接 target、图片懒加载、文章结尾版权声明等） |
| `toc` | 目录 HTML（按标题生成） |
| `comment_status` | `o` 开放 / `c` 关闭 |
| `show_toc` | 是否显示目录 |
| `comment_count` | 已启用评论数 |
| `prev_article` / `next_article` | 前/后一篇：`{id, title, url}` 或 `null` |
| `seo_title` / `seo_description` / `seo_keywords` | SEO 字段 |

**错误**：`404` 文章不存在（草稿/页面类型不通过本接口暴露）。

### 3.3 新建文章 `POST /api/article_create`

**权限**：仅管理员（IsAdminUser）

**请求体**（JSON，`author` 自动取当前用户）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 标题（唯一） |
| `body` | string | 是 | 正文 **Markdown 源文本** |
| `type` | string | 否 | `a` 文章（默认）/ `p` 页面 |
| `status` | string | 否 | `p` 发布（默认）/ `d` 草稿 |
| `comment_status` | string | 否 | `o` / `c`，默认 `o` |
| `show_toc` | boolean | 否 | 默认 false |
| `is_top` | boolean | 否 | 默认 false |
| `category` | int | 是 | 分类 id |
| `tags` | int[] | 否 | 标签 id 列表 |

**响应** `201`：完整文章详情对象（同 3.2）。

### 3.4 文章导出

- **单篇** `GET /api/articles/<pk>/export/`
  - 仅可导出**已发布文章**（防匿名越权导出草稿）。
  - 响应：`text/markdown` 附件下载（`.md`，含 YAML front matter：title/date/category/tags）。
- **批量** `GET /api/articles/export/?ids=1,2,3`
  - 响应：`application/zip`（`articles.zip`，内含多个 `.md`）。
  - 错误：`400` 未提供 ids / 格式错误；`404` 无匹配文章。

### 3.5 文章导入解析 `POST /api/articles/import/`

**权限**：仅管理员；**格式**：`multipart/form-data`（字段 `file`，`.md` ≤10MB）

**说明**：解析 Markdown（支持 YAML front matter 与纯 Markdown），**返回结构化数据供前端填充编辑表单，不直接入库**。

**响应** `200`：

```json
{ "title": "...", "category": "...", "tags": ["..."], "date": "...", "body": "..." }
```

**错误**：`400` 非 .md / 超大小 / 非 UTF-8 编码。

### 3.6 草稿箱

**权限**：全部仅管理员（IsAdminUser）。数据源：`type='a', status='d'`，按 `-last_modify_time` 排序。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/drafts/` | 草稿列表（分页信封，列表字段） |
| GET | `/api/drafts/<pk>/` | 草稿详情（ArticleCreateSerializer：含 body/title/category/tags 等编辑字段） |
| PATCH / PUT | `/api/drafts/<pk>/` | 更新草稿（字段同 3.3） |
| DELETE | `/api/drafts/<pk>/` | 删除草稿 |
| POST | `/api/drafts/<pk>/publish/` | **发布草稿**：`status` 置为 `p`，返回完整详情 |

### 3.7 分类

- `GET /api/categories/`：分类列表。**lookup_field = slug**。每项含 `article_count`（**直接归属**该分类的已发布文章数，非递归）、`child_categories`（递归子分类树）、SEO 字段。
- `GET /api/categories/<slug>/`：分类详情（同字段）。
- 均公开读。

### 3.8 标签

- `GET /api/tags/`：标签列表，含 `article_count`（已发布文章数）、SEO 字段。
- `GET /api/tags/<slug>/`：标签详情。
- 均公开读。

### 3.9 友情链接 `GET /api/links/`

**权限**：公开读。仅返回 `is_enable=true`。字段：`id, name, link, sequence, is_enable, show_type`（分页信封）。

### 3.10 侧边栏 `GET /api/sidebars/`

**权限**：公开读。仅返回 `is_enable=true`。字段：`id, name, content, sequence, is_enable`（分页信封）。

### 3.11 博客设置 `GET /api/settings/`

**权限**：公开读（只读）。返回**单条**配置（非分页）：

```json
{
  "id": 1, "site_name": "WhrBlog", "site_description": "...", "site_seo_description": "...",
  "site_keywords": "...", "article_sub_length": 300, "sidebar_article_count": 10,
  "sidebar_comment_count": 5, "article_comment_count": 5,
  "color_scheme": "purple", "open_site_comment": true, "show_google_adsense": false
}
```

### 3.12 搜索 `GET /api/search/?q=关键词`

**权限**：公开读。

**说明**：优先使用 **Elasticsearch** 全文检索（高亮、相关性排序），ES 不可用或出错时自动回退 ORM `title/body` 模糊查询。仅搜已发布文章。

**查询参数**：`q`（关键词）、`page`（默认 1）、`page_size`（默认 20，**上限 50**）。

**响应**（独立分页结构，非标准信封）：

```json
{
  "query": "django",
  "total": 12,
  "page": 1,
  "page_size": 20,
  "results": [ "文章列表字段（ES 命中时附加 highlight / score）" ]
}
```

### 3.13 侧边栏聚合 `GET /api/sidebar/?linktype=p`

**权限**：公开。聚合最新文章、阅读排行、分类、链接、标签云、附加侧边栏、广告位等（结果缓存 5 分钟）。

**查询参数**：`linktype`（链接显示位置：`i/l/p/a/s`，默认 `p`）、`article_id`（可选，指定后标签云只取该文章标签）。

**响应**字段：

| 字段 | 说明 |
|------|------|
| `recent_articles` | 最新 5 篇（列表字段） |
| `most_read_articles` | 阅读排行前 5（按 views） |
| `sidebar_categorys` | 分类前 5（含 article_count） |
| `links` | 启用且匹配 linktype 的友链 |
| `sidebar_tags` | 标签云 top 20：`{id, name, slug, count, size, url}` |
| `extra_sidebars` | 启用侧边栏：`{id, name, content_html, sequence}` |
| `show_google_adsense` / `google_adsense_codes` / `open_site_comment` / `show_gongan_code` | 站点配置项 |

### 3.14 站点全局信息 `GET /api/siteinfo/`

**权限**：公开。返回导航栏所需的全量站点信息：

```json
{
  "SITE_NAME": "WhrBlog",
  "SITE_DESCRIPTION": "...", "SITE_SEO_DESCRIPTION": "...", "SITE_KEYWORDS": "...",
  "SITE_BASE_URL": "http://127.0.0.1:8000/",
  "CURRENT_YEAR": 2026,
  "BEIAN_CODE": "...", "BEIAN_CODE_GONGAN": "...", "SHOW_GONGAN_CODE": false,
  "ANALYTICS_CODE": "...", "GLOBAL_HEADER": "...", "GLOBAL_FOOTER": "...",
  "COLOR_SCHEME": "purple", "OPEN_SITE_COMMENT": true,
  "SHOW_GOOGLE_ADSENSE": false, "GOOGLE_ADSENSE_CODES": "...", "COMMENT_NEED_REVIEW": false,
  "ARTICLE_SUB_LENGTH": 300,
  "nav_category_list": [ { "id": 1, "name": "Python", "slug": "python", "url": "/category/python",
      "parent_category": null, "article_count": 40, "child_categories": [ ... ] } ],
  "nav_tags": [ { "id": 1, "name": "python", "slug": "python", "url": "/tag/python", "article_count": 30 } ],
  "nav_pages": [ { "id": 500, "title": "关于我", "url": "/article/500" } ]
}
```

> `nav_category_list` 仅返回顶级分类；`article_count` 为**含子孙分类的递归总篇数**。

### 3.15 图床上传 `POST /api/upload`（兼容旧路径 `/upload`）

**权限**：仅管理员；**格式**：`multipart/form-data`，支持多文件（每个字段名一个文件）。

**限制**：单文件 ≤10MB；仅 `jpg/jpeg/png/gif/bmp/webp`；Pillow 校验并压缩（quality=85），非法图片删除文件并 `400`。

**响应** `200`：**URL 数组**（非对象）：

```json
[ "/media/image/2026/08/21/<uuid>.png" ]
```

**错误**：`400` 文件过大 / 格式不支持 / 非法路径 / 无效图片。

### 3.16 清理缓存 `POST /api/clean_cache`

**权限**：仅管理员。清除 Redis 全量缓存。

**响应** `200`：`{"success": true, "message": "缓存已清理"}`

---

## 四、comments —— 评论模块

### 4.1 评论列表 `GET /api/comments/`

**权限**：公开读。仅返回 `is_enable=true`（审核通过/无需审核）的评论，按 `-id` 排序。

**查询参数**：

| 参数 | 说明 |
|------|------|
| `article` | 按文章 id 筛选 |
| `parent` | 按父评论 id 筛选（只看某条评论的回复） |
| `page` / `page_size` | 分页 |

**响应**（分页信封，`results` 元素）：

```json
{
  "id": 1,
  "body": "评论内容（≤300 字）",
  "author": { "id": 2, "username": "whr", "nickname": "", "is_admin": true },
  "article": 497,
  "parent_id": null,
  "creation_time": "2026-08-21T12:00:00+08:00",
  "is_enable": true,
  "reactions": {
    "👍": { "count": 5, "has_reacted": false, "users": ["Alice", "Bob"] },
    "❤️": { "count": 2, "has_reacted": true, "users": ["whr"] }
  },
  "reply_count": 3
}
```

### 4.2 评论详情 `GET /api/comments/<id>/`

**权限**：公开读。字段同列表项。

### 4.3 提交评论 `POST /api/comments/`

**权限**：需登录（写操作）。

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `article` 或 `article_id` | int | 是 | 文章 id |
| `body` 或 `content` | string | 是 | 内容，≤300 字 |
| `parent_id` | int | 否 | 回复的父评论 id（须属于同一篇文章） |

**行为**：文章评论关闭（`comment_status='c'`）或非已发布文章 → `400 该文章评论已关闭`；`is_enable` 取决于站点配置 `comment_need_review`（需审核则新评论 `is_enable=false`，审核前列表不可见）。

**响应** `201`：新评论详情对象（同 4.1）。

**错误**：`400` 内容为空 / 超 300 字 / 评论关闭 / 父评论无效；`404` 文章不存在 / 父评论不存在。

### 4.4 评论 Emoji 反应

**路径**：`/api/comments/<id>/react/`

- `GET`：查看该评论的 reactions 汇总（匿名时 `has_reacted` 恒为 false）。
- `POST`：**切换**点赞/表情（已点则取消）。需登录。
  - 请求体：`{"reaction_type": "👍"}`，可选值：`👍 👎 ❤️ 😄 🎉 😕 🚀 👀`
  - 响应 `200`：

```json
{ "success": true, "action": "added | removed", "reactions": { "👍": { "count": 3, "has_reacted": true, "users": [...] } } }
```

  - 错误：`400` 非法 reaction_type。

---

## 五、system —— 系统级接口

| 路径 | 说明 |
|------|------|
| `GET /health/` | 健康检查：`{"status": "healthy", "timestamp": <unix秒>}`（无认证） |
| `GET /sitemap.xml` | 站点地图（blog/category/tag/user/static） |
| `GET /admin/` | Django Admin 后台（管理员） |
| `GET /media/<path>` | 上传文件（头像、图床图片）。开发环境由 Django serve；生产由 Nginx `/media/` 代理 |
| `GET /static/<path>` | 前端静态资源（生产经 `collectstatic`） |

---

## 六、接口速查表

### accounts（12 个 JSON API）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | /api/register | 公开 | 注册（含验证码） |
| POST | /api/send_register_code | 公开 | 发送注册验证码 |
| POST | /api/login | 公开 | 登录 |
| POST | /api/logout | 登录 | 登出 |
| GET/PATCH | /api/user | 登录 | 用户信息 / 改昵称 |
| POST | /api/verify_email | 公开 | 邮箱激活 |
| POST | /api/resend_verify_email | 公开 | 重发注册验证码 |
| POST | /api/forget_password_code | 公开 | 发忘记密码验证码 |
| POST | /api/forget_password | 公开 | 重置密码 |
| POST | /api/change_password | 登录 | 改密码 |
| POST | /api/change_email | 登录 | 改邮箱 |
| POST | /api/upload_avatar | 登录 | 上传头像 |

### blog（20 个 JSON API）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/articles/ | 公开读 | 文章列表（分页/筛选） |
| GET | /api/articles/<id>/ | 公开读 | 文章详情（含 HTML/SEO/前后篇） |
| POST | /api/article_create | 管理员 | 新建文章 |
| GET | /api/articles/export/ | 公开读 | 批量导出 zip |
| GET | /api/articles/<pk>/export/ | 公开读 | 单篇导出 md |
| POST | /api/articles/import/ | 管理员 | Markdown 导入解析 |
| GET | /api/drafts/ | 管理员 | 草稿列表 |
| GET | /api/drafts/<pk>/ | 管理员 | 草稿详情 |
| PATCH/PUT | /api/drafts/<pk>/ | 管理员 | 更新草稿 |
| DELETE | /api/drafts/<pk>/ | 管理员 | 删除草稿 |
| POST | /api/drafts/<pk>/publish/ | 管理员 | 发布草稿 |
| GET | /api/categories/ | 公开读 | 分类列表 |
| GET | /api/categories/<slug>/ | 公开读 | 分类详情 |
| GET | /api/tags/ | 公开读 | 标签列表 |
| GET | /api/tags/<slug>/ | 公开读 | 标签详情 |
| GET | /api/links/ | 公开读 | 友情链接 |
| GET | /api/sidebars/ | 公开读 | 侧边栏 |
| GET | /api/settings/ | 公开读 | 站点设置（单条） |
| GET | /api/search/ | 公开读 | 搜索（ES/ORM 兜底） |
| GET | /api/sidebar/ | 公开 | 侧边栏聚合 |
| GET | /api/siteinfo/ | 公开 | 站点全局信息 |
| POST | /api/upload | 管理员 | 图床上传 |
| POST | /api/clean_cache | 管理员 | 清理缓存 |

### comments（5 个 JSON API）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/comments/ | 公开读 | 评论列表（按文章/父评论筛选） |
| GET | /api/comments/<id>/ | 公开读 | 评论详情 |
| POST | /api/comments/ | 登录 | 提交评论 |
| GET | /api/comments/<id>/react/ | 公开读 | 查看 reactions |
| POST | /api/comments/<id>/react/ | 登录 | 切换 reaction |
