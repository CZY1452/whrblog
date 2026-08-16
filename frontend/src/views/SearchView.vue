<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiGet } from '../api.js';
import { setSeo } from '../seo.js';

const route = useRoute();
const router = useRouter();

const query = ref(route.query.q || '');
const results = ref([]);
const searched = ref(false);
const loading = ref(false);
const error = ref(null);

const page = ref(Number(route.query.page) || 1);
const total = ref(0);
const pageSize = ref(20);

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

async function doSearch(p = 1) {
  const q = query.value.trim();
  if (!q) return;
  loading.value = true;
  error.value = null;
  page.value = p;
  try {
    const data = await apiGet(`/api/search/?q=${encodeURIComponent(q)}&page=${p}&page_size=${pageSize.value}`);
    results.value = data.results || [];
    total.value = data.total || 0;
    if (data.page_size) pageSize.value = data.page_size;
    searched.value = true;
    setSeo({
      title: `搜索：${q} | WhrBlog`,
      description: `搜索"${q}"的结果。`,
      ogType: 'website',
    });
    router.replace({ query: { q, page: p > 1 ? p : undefined } });
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/**
 * 只保留 <em> 标签，剥离其余所有 HTML，防止 ES 高亮内容中的 XSS
 */
function sanitizeHtml(html) {
  if (!html) return '';
  return html.replace(/<\/?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>/g, (match, tag) => {
    return tag.toLowerCase() === 'em' ? match : '';
  });
}

function titleHtml(a) {
  const raw = a.highlight?.title?.[0] || a.title;
  return sanitizeHtml(raw);
}

function summaryHtml(a) {
  const raw = a.highlight?.body?.[0] || a.summary || '';
  return sanitizeHtml(raw);
}

onMounted(() => {
  setSeo({ title: '搜索 | WhrBlog', description: '在本站搜索文章内容。', ogType: 'website' });
  if (query.value) doSearch(page.value);
});
</script>

<template>
  <div class="space-y-5">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-5">
      <h1 class="text-xl font-bold mb-4">搜索文章</h1>
      <form @submit.prevent="doSearch(1)" class="flex gap-2">
        <input v-model="query" type="search" placeholder="输入关键词…"
          class="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900" />
        <button type="submit" :disabled="loading"
          class="px-5 py-2 rounded-lg text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
          搜索
        </button>
      </form>
    </div>

    <div v-if="loading" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-gray-400">搜索中…</div>
    <div v-else-if="error" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-red-500">{{ error }}</div>
    <template v-else>
      <div v-if="searched && !results.length" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-gray-400">没有找到相关文章</div>
      <div v-if="searched && total > 0" class="text-xs text-gray-400 px-1">共 {{ total }} 条结果</div>
      <div v-for="a in results" :key="a.id" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5">
        <h2 class="text-lg font-semibold">
          <router-link :to="a.url" class="hover:text-blue-600 dark:hover:text-blue-400" v-html="titleHtml(a)"></router-link>
        </h2>
        <div class="text-xs text-gray-400 mt-1">{{ a.author?.nickname || a.author?.username }} · {{ formatDate(a.pub_time) }} · {{ a.views }} 阅读</div>
        <p class="text-sm text-gray-600 dark:text-gray-300 mt-2 search-snippet" v-html="summaryHtml(a)"></p>
      </div>

      <div v-if="totalPages > 1" class="flex justify-center gap-2 pt-2">
        <button v-if="page > 1" @click="doSearch(page - 1)"
          class="px-3 py-1 rounded text-sm border border-gray-200 dark:border-slate-700 hover:bg-gray-100 dark:hover:bg-slate-700">上一页</button>
        <span class="px-3 py-1 text-sm text-gray-500">{{ page }} / {{ totalPages }}</span>
        <button v-if="page < totalPages" @click="doSearch(page + 1)"
          class="px-3 py-1 rounded text-sm border border-gray-200 dark:border-slate-700 hover:bg-gray-100 dark:hover:bg-slate-700">下一页</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
:deep(em) {
  color: #e53e3e;
  font-style: normal;
  font-weight: 600;
  background: rgba(229, 62, 62, 0.08);
  padding: 0 2px;
  border-radius: 2px;
}
</style>