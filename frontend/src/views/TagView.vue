<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiGet } from '../api.js';
import { setSeo } from '../seo.js';

const route = useRoute();
const router = useRouter();
const slug = () => route.params.slug;

const meta = ref(null);
const articles = ref([]);
const loading = ref(true);
const error = ref(null);
const page = ref(Number(route.query.page) || 1);
const count = ref(0);
const pageSize = ref(10);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [t, list] = await Promise.all([
      apiGet(`/api/tags/${slug()}/`),
      apiGet(`/api/articles/?tag=${encodeURIComponent(slug())}&page=${page.value}`),
    ]);
    meta.value = t;
    articles.value = list.results || [];
    count.value = list.count || 0;
    if (list.page_size) pageSize.value = list.page_size;
    setSeo({
      title: t.seo_title,
      description: t.seo_description,
      ogType: 'website',
    });
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(count.value / pageSize.value)));

function goToPage(p) {
  if (p < 1 || p > totalPages.value) return;
  page.value = p;
  router.replace({ query: { page: p > 1 ? p : undefined } });
  load();
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

watch(() => route.params.slug, () => {
  page.value = 1;
  load();
});
watch(() => route.query.page, (v) => {
  const p = Number(v) || 1;
  if (p !== page.value) {
    page.value = p;
    load();
  }
});
onMounted(load);
</script>

<template>
  <div class="space-y-5">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-5">
      <h1 class="text-xl font-bold">标签：{{ meta?.name }}</h1>
      <p class="text-sm text-gray-500 mt-1">{{ meta?.seo_description }}</p>
    </div>

    <div v-if="loading" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-gray-400">加载中…</div>
    <div v-else-if="error" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-red-500">{{ error }}</div>
    <template v-else>
      <div v-if="!articles.length" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-gray-400">该标签下暂无文章</div>
      <div v-for="a in articles" :key="a.id" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5">
        <h2 class="text-lg font-semibold">
          <router-link :to="a.url" class="hover:text-blue-600 dark:hover:text-blue-400">{{ a.title }}</router-link>
          <span v-if="a.is_top" class="inline-block align-middle ml-2 px-1.5 py-0.5 rounded bg-amber-400/90 text-white text-xs font-medium">置顶</span>
        </h2>
        <div class="text-xs text-gray-400 mt-1">{{ a.author?.nickname || a.author?.username }} · {{ formatDate(a.pub_time) }} · {{ a.views }} 阅读</div>
        <p class="text-sm text-gray-600 dark:text-gray-300 mt-2">{{ a.summary }}</p>
      </div>

      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 pt-4">
        <button @click="goToPage(page - 1)" :disabled="page <= 1"
          class="px-3 py-1 rounded text-sm bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 disabled:opacity-40">
          上一页
        </button>
        <span class="text-sm text-gray-500">第 {{ page }} / {{ totalPages }} 页</span>
        <button @click="goToPage(page + 1)" :disabled="page >= totalPages"
          class="px-3 py-1 rounded text-sm bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 disabled:opacity-40">
          下一页
        </button>
      </div>
    </template>
  </div>
</template>