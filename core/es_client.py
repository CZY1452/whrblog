"""
Elasticsearch 客户端与索引管理
提供 ES 连接、索引创建/删除、文档索引/删除、全文搜索等功能
"""
import logging

from django.conf import settings
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 客户端单例
# ---------------------------------------------------------------------------

_client = None


def get_es_client():
    """获取 ES 客户端单例"""
    global _client
    if _client is None:
        cfg = settings.ELASTICSEARCH_DSL
        _client = Elasticsearch(
            hosts=[cfg['hosts']],
            basic_auth=cfg.get('basic_auth'),
            verify_certs=cfg.get('verify_certs', False),
            ssl_show_warn=cfg.get('ssl_show_warn', False),
            request_timeout=10,
        )
    return _client


def get_index_name():
    """获取索引名称"""
    return getattr(settings, 'ELASTICSEARCH_INDEX', 'whrblog')


# ---------------------------------------------------------------------------
# 索引 Mapping 定义
# ---------------------------------------------------------------------------

# 中文分词：索引时用 ik_max_word（最细粒度，召回高），检索时用 ik_smart（智能切分，精准）
_IK_TEXT = {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_smart"}
_IK_TEXT_KW = {
    "type": "text",
    "analyzer": "ik_max_word",
    "search_analyzer": "ik_smart",
    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
}

ARTICLE_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "title": {**_IK_TEXT_KW},
            "body": {**_IK_TEXT},
            "summary": {**_IK_TEXT},
            "status": {"type": "keyword"},
            "type": {"type": "keyword"},
            "pub_time": {"type": "date"},
            "views": {"type": "integer"},
            "author": {
                "properties": {
                    "id": {"type": "integer"},
                    "username": {"type": "keyword"},
                    "nickname": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                }
            },
            "category": {
                "properties": {
                    "id": {"type": "integer"},
                    "name": {**_IK_TEXT_KW},
                    "slug": {"type": "keyword"},
                }
            },
            "tags": {
                "properties": {
                    "id": {"type": "integer"},
                    "name": {**_IK_TEXT_KW},
                    "slug": {"type": "keyword"},
                }
            },
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "default": {"type": "ik_max_word"}
            }
        }
    }
}


# ---------------------------------------------------------------------------
# 索引操作
# ---------------------------------------------------------------------------

def ensure_index():
    """确保索引存在，不存在则创建"""
    client = get_es_client()
    index = get_index_name()
    if not client.indices.exists(index=index):
        client.indices.create(index=index, body=ARTICLE_MAPPING)
        logger.info('Created ES index: %s', index)


def delete_index():
    """删除索引"""
    client = get_es_client()
    index = get_index_name()
    if client.indices.exists(index=index):
        client.indices.delete(index=index)
        logger.info('Deleted ES index: %s', index)


def recreate_index():
    """重建索引（先删后建）"""
    delete_index()
    ensure_index()


# ---------------------------------------------------------------------------
# 文档操作
# ---------------------------------------------------------------------------

def _clean_text_for_index(text):
    """去除 HTML 标签与常见 Markdown 语法符号，压缩空白，得到适合分词的纯文本"""
    import re
    from django.utils.html import strip_tags
    if not text:
        return ''
    text = strip_tags(text)
    # 去掉常见 Markdown 语法符号（图片/链接/加粗/斜体/行内代码/标题/引用等）
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)          # 图片
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)        # 链接保留文字
    text = re.sub(r'[`*_>#~|]', ' ', text)                       # 行内代码/加粗/标题等
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _build_article_doc(article):
    """将 Article 模型实例转换为 ES 文档"""
    tags = [{'id': t.id, 'name': t.name, 'slug': t.slug}
            for t in article.tags.all()]
    category = article.category
    body_text = _clean_text_for_index(article.body)
    # 生成摘要（取前 500 字符）
    summary = body_text[:500] if body_text else ''

    return {
        'id': article.id,
        'title': article.title,
        'body': body_text,
        'summary': summary,
        'status': article.status,
        'type': article.type,
        'pub_time': article.pub_time.isoformat() if article.pub_time else None,
        'views': article.views,
        'author': {
            'id': article.author.id,
            'username': article.author.username,
            'nickname': article.author.nickname or article.author.username,
        },
        'category': {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
        },
        'tags': tags,
    }


def index_article(article):
    """索引单篇文章（仅已发布文章）"""
    if article.status != 'p' or article.type != 'a':
        # 非已发布文章从 ES 中移除
        remove_article(article.id)
        return

    client = get_es_client()
    index = get_index_name()
    doc = _build_article_doc(article)
    client.index(index=index, id=article.id, document=doc)
    logger.debug('Indexed article %d: %s', article.id, article.title)


def remove_article(article_id):
    """从 ES 中移除文章"""
    from elasticsearch import NotFoundError
    client = get_es_client()
    index = get_index_name()
    try:
        client.delete(index=index, id=article_id)
        logger.debug('Removed article %d from ES', article_id)
    except NotFoundError:
        logger.debug('Article %d not found in ES (already removed)', article_id)
    except Exception:
        logger.warning('Failed to remove article %d from ES', article_id)


def bulk_index_articles(articles):
    """批量索引文章"""
    client = get_es_client()
    index = get_index_name()
    actions = []
    for article in articles:
        if article.status == 'p' and article.type == 'a':
            doc = _build_article_doc(article)
            actions.append({'index': {'_index': index, '_id': article.id}})
            actions.append(doc)

    if actions:
        # refresh=False：批量索引后不强制刷新，让 ES 按默认 refresh_interval 合并刷盘，
        # 显著提升大批量导入吞吐；如需立即可见可在调用后手动刷新
        client.bulk(operations=actions, refresh=False)
        count = len(actions) // 2
        logger.info('Bulk indexed %d articles', count)
        return count
    return 0


# ---------------------------------------------------------------------------
# 搜索
# ---------------------------------------------------------------------------

def search_articles(query, page=1, page_size=20):
    """
    全文搜索文章
    搜索范围：标题（权重高）、正文、分类名、标签名
    返回格式：{'total': int, 'results': [{'id': int, 'score': float}, ...]}
    """
    client = get_es_client()
    index = get_index_name()

    body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "title^5",
                                "category.name^3",
                                "tags.name^2",
                                "body",
                                "summary",
                            ],
                            "type": "best_fields",
                            "tie_breaker": 0.3,
                            "fuzziness": "AUTO",
                        }
                    }
                ],
                # 短语完整匹配加权：标题/正文中包含完整查询词组的结果排得更前
                "should": [
                    {"match_phrase": {"title": {"query": query, "boost": 3}}},
                    {"match_phrase": {"body": {"query": query, "boost": 1.5}}},
                ],
                # 只返回已发布的文章，兜底保证结果可用性
                "filter": [
                    {"term": {"status": "p"}},
                    {"term": {"type": "a"}},
                ],
            }
        },
        "highlight": {
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
            "require_field_match": False,
            "fields": {
                "title": {"number_of_fragments": 0},
                "body": {"fragment_size": 150, "number_of_fragments": 2},
            },
        },
        "_source": ["id", "title", "summary", "pub_time", "views",
                     "author", "category", "tags"],
        "sort": [
            {"_score": "desc"},
            {"pub_time": "desc"},
        ],
        "from": (page - 1) * page_size,
        "size": page_size,
    }

    result = client.search(index=index, body=body)
    total = result['hits']['total']['value']
    hits = result['hits']['hits']

    results = []
    for hit in hits:
        item = hit['_source']
        item['score'] = hit['_score']
        if 'highlight' in hit:
            item['highlight'] = hit['highlight']
        results.append(item)

    return {'total': total, 'results': results}


def is_available():
    """检查 ES 服务是否可用（结果缓存 30 秒）"""
    from django.core.cache import cache
    cached = cache.get('es_available')
    if cached is not None:
        return cached
    try:
        client = get_es_client()
        ok = client.ping()
    except Exception:
        ok = False
    cache.set('es_available', ok, 30)
    return ok
