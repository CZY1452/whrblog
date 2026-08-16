<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { apiGet, apiPost, apiDownloadFile, getCsrfToken, extractError } from '../api.js';
import { setSeo } from '../seo.js';

const route = useRoute();
const articleId = computed(() => route.params.id);

const data = ref(null);
const loading = ref(true);
const error = ref(null);

// ===== 评论 =====
const allComments = ref([]);
const commentsLoading = ref(true);
const commentsError = ref(null);
const replyingTo = ref(null);
const replyContent = ref('');
const newComment = ref('');
const submitting = ref(false);
const replySubmitting = ref(false);
const page = ref(1);
const count = ref(0);

const REACTION_EMOJIS = ['👍', '👎', '❤️', '😄', '🎉', '😕', '🚀', '👀'];

async function load() {
  loading.value = true;
  error.value = null;
  try {
    data.value = await apiGet(`/api/articles/${articleId.value}/`);
    setSeo({
      title: data.value.seo_title,
      description: data.value.seo_description,
      keywords: data.value.seo_keywords,
      ogType: 'article',
      ogUrl: window.location.href,
    });
    if (commentsOpen.value) await loadComments();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
    commentsLoading.value = false;
  }
}

const commentsOpen = computed(() => {
  return data.value && data.value.comment_status === 'o';
});

async function loadComments() {
  commentsLoading.value = true;
  commentsError.value = null;
  try {
    const res = await fetch(`/api/comments/?article=${articleId.value}&page=${page.value}`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) throw new Error(`加载失败 (${res.status})`);
    const d = await res.json();
    allComments.value = d.results || [];
    count.value = d.count || 0;
  } catch (e) {
    commentsError.value = e.message;
  } finally {
    commentsLoading.value = false;
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(count.value / 10)));

function roots() {
  return allComments.value.filter(c => !c.parent_id);
}
function childrenOf(id) {
  return allComments.value.filter(c => c.parent_id === id);
}
function isSuperuser(c) {
  return c && c.author && !!c.author.is_admin;
}
function formatDateTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function toggleReply(commentId) {
  replyingTo.value = replyingTo.value === commentId ? null : commentId;
  replyContent.value = '';
}
function cancelReply() {
  replyingTo.value = null;
  replyContent.value = '';
}

async function submitComment() {
  if (!newComment.value.trim() || submitting.value) return;
  submitting.value = true;
  commentsError.value = null;
  try {
    await apiPost('/api/comments/', { article_id: articleId.value, content: newComment.value });
    newComment.value = '';
    page.value = 1;
    await loadComments();
    notify('评论成功！');
  } catch (e) {
    notify('提交失败：' + e.message, true);
  } finally {
    submitting.value = false;
  }
}

async function submitReply(commentId) {
  if (!replyContent.value.trim() || replySubmitting.value) return;
  replySubmitting.value = true;
  try {
    await apiPost('/api/comments/', { article_id: articleId.value, content: replyContent.value, parent_id: commentId });
    replyContent.value = '';
    replyingTo.value = null;
    await loadComments();
    notify('回复成功！');
  } catch (e) {
    notify('提交失败：' + e.message, true);
  } finally {
    replySubmitting.value = false;
  }
}

async function toggleReaction(comment, reactionType) {
  const res = await fetch(`/api/comments/${comment.id}/react/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
      'Accept': 'application/json',
    },
    body: JSON.stringify({ reaction_type: reactionType }),
  });
  if (res.status === 401) {
    window.location.href = '/login';
    return;
  }
  if (!res.ok) return;
  const d = await res.json();
  comment.reactions = d.reactions || {};
}

function countReaction(c, emoji) {
  const r = c.reactions || {};
  const key = Object.keys(r).find(k => (r[k]?.emoji || k) === emoji);
  return key ? (r[key]?.count || 0) : 0;
}

function notify(message, isError = false) {
  const el = document.createElement('div');
  el.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white ${isError ? 'bg-red-500' : 'bg-green-500'}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => {
    el.classList.add('opacity-0', 'transition-opacity', 'duration-300');
    setTimeout(() => el.remove(), 300);
  }, 3000);
}

const exporting = ref(false);

async function exportArticle() {
  exporting.value = true;
  try {
    await apiDownloadFile(`/api/articles/${articleId.value}/export/`);
  } catch (e) {
    notify('导出失败：' + e.message, true);
  } finally {
    exporting.value = false;
  }
}

onMounted(load);

watch(articleId, () => {
  data.value = null;
  error.value = null;
  loading.value = true;
  allComments.value = [];
  commentsError.value = null;
  commentsLoading.value = true;
  replyingTo.value = null;
  replyContent.value = '';
  newComment.value = '';
  page.value = 1;
  count.value = 0;
  load();
});
</script>

<template>
  <div>
    <div v-if="loading" class="space-y-3">
      <div class="h-6 bg-gray-200 dark:bg-slate-700 rounded w-1/2"></div>
      <div class="h-40 bg-gray-200 dark:bg-slate-700 rounded"></div>
    </div>
    <div v-else-if="error" class="text-red-500">文章不存在或加载失败：{{ error }}</div>
    <article v-else class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 md:p-8">
      <h1 class="text-2xl md:text-3xl font-bold mb-2">{{ data.title }}</h1>
      <div class="text-xs text-gray-400 mb-4 flex flex-wrap items-center gap-2">
        <span>{{ data.author?.nickname || data.author?.username }}</span>
        <span>{{ formatDate(data.pub_time) }}</span>
        <span v-if="data.category">
          <router-link :to="data.category.url">{{ data.category.name }}</router-link>
        </span>
        <span>{{ data.views }} 阅读 · {{ data.comment_count }} 评论</span>
        <button @click="exportArticle" :disabled="exporting"
          class="ml-auto px-2 py-0.5 rounded border border-gray-200 dark:border-slate-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 disabled:opacity-40">
          {{ exporting ? '导出中…' : '导出 .md' }}
        </button>
      </div>

      <div class="prose dark:prose-invert max-w-none border-t border-gray-100 dark:border-slate-700 pt-4"
        v-html="data.body"></div>

      <div v-if="data.tags && data.tags.length" class="mt-4 flex flex-wrap gap-1">
        <router-link v-for="t in data.tags" :key="t.id" :to="t.url"
          class="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300">
          #{{ t.name }}
        </router-link>
      </div>

      <nav v-if="data.prev_article || data.next_article" class="mt-6 pt-4 border-t border-gray-100 dark:border-slate-700 flex flex-col sm:flex-row justify-between gap-2 text-sm">
        <router-link v-if="data.prev_article" :to="data.prev_article.url" class="text-gray-500 hover:text-blue-600">
          ← 上一篇：{{ data.prev_article.title }}
        </router-link>
        <span v-else></span>
        <router-link v-if="data.next_article" :to="data.next_article.url" class="text-gray-500 hover:text-blue-600">
          下一篇：{{ data.next_article.title }} →
        </router-link>
      </nav>
    </article>

    <!-- 评论区 -->
    <section v-if="data && commentsOpen" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 mt-5">
      <h2 class="text-lg font-semibold mb-4">评论（{{ count }}）</h2>

      <form @submit.prevent="submitComment" class="mb-6">
        <textarea v-model="newComment" rows="3"
          class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900"
          placeholder="写下你的评论…"></textarea>
        <div class="mt-2 flex items-center gap-3">
          <button type="submit" :disabled="submitting"
            class="px-4 py-2 rounded text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
            {{ submitting ? '提交中…' : '发表评论' }}
          </button>
        </div>
      </form>

      <div v-if="commentsLoading" class="text-sm text-gray-400">加载评论中…</div>
      <div v-else-if="commentsError" class="text-sm text-red-500">{{ commentsError }}</div>
      <div v-else-if="!allComments.length" class="text-sm text-gray-400">暂无评论，快来抢沙发吧~</div>

      <ul v-else class="space-y-4">
        <li v-for="c in roots()" :key="c.id">
          <div class="flex gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 text-sm">
                <span class="font-medium">{{ c.author?.nickname || c.author?.username }}</span>
                <span v-if="isSuperuser(c)" class="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300">博主</span>
                <span class="text-xs text-gray-400">{{ formatDateTime(c.creation_time) }}</span>
              </div>
              <p class="text-sm mt-1 text-gray-700 dark:text-gray-300">{{ c.body }}</p>
              <div class="mt-1 flex items-center gap-2">
                <button @click="toggleReply(c.id)" class="text-xs text-gray-400 hover:text-blue-600">回复</button>
                <button v-for="emoji in REACTION_EMOJIS.slice(0, 4)" :key="emoji" @click="toggleReaction(c, emoji)"
                  class="text-xs text-gray-400 hover:text-blue-600">
                  {{ emoji }} {{ countReaction(c, emoji) || '' }}
                </button>
              </div>

              <!-- 回复框 -->
              <div v-if="replyingTo === c.id" class="mt-2">
                <textarea v-model="replyContent" rows="2"
                  class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-2 text-sm bg-white dark:bg-slate-900"
                  :placeholder="'回复 ' + (c.author?.nickname || c.author?.username) + '…'"></textarea>
                <div class="mt-1 flex gap-2">
                  <button @click="submitReply(c.id)" :disabled="replySubmitting"
                    class="px-3 py-1 rounded text-xs bg-blue-600 text-white disabled:opacity-40">回复</button>
                  <button @click="cancelReply" class="px-3 py-1 rounded text-xs bg-gray-100 dark:bg-slate-700 text-gray-600">取消</button>
                </div>
              </div>

              <!-- 子评论 -->
              <ul v-if="childrenOf(c.id).length" class="mt-3 space-y-3 border-l-2 border-gray-100 dark:border-slate-700 pl-4">
                <li v-for="child in childrenOf(c.id)" :key="child.id">
                  <div class="flex gap-2">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 text-xs">
                        <span class="font-medium">{{ child.author?.nickname || child.author?.username }}</span>
                        <span class="text-gray-400">{{ formatDateTime(child.creation_time) }}</span>
                      </div>
                      <p class="text-sm mt-0.5 text-gray-600 dark:text-gray-300">{{ child.body }}</p>
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </li>
      </ul>

      <div v-if="totalPages > 1" class="mt-4 flex items-center justify-center gap-2">
        <button @click="page--; loadComments()" :disabled="page <= 1"
          class="px-3 py-1 rounded text-xs bg-gray-100 dark:bg-slate-700 disabled:opacity-40">上一页</button>
        <span class="text-xs text-gray-500">{{ page }} / {{ totalPages }}</span>
        <button @click="page++; loadComments()" :disabled="page >= totalPages"
          class="px-3 py-1 rounded text-xs bg-gray-100 dark:bg-slate-700 disabled:opacity-40">下一页</button>
      </div>
    </section>
  </div>
</template>