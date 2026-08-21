<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiGet } from '../api.js';
import { setSeo } from '../seo.js';
import { useSiteStore } from '../stores/site.js';

const route = useRoute();
const router = useRouter();
const siteStore = useSiteStore();

const articles = ref([]);
const loading = ref(true);
const error = ref(null);
const count = ref(0);
const page = ref(parseInt(route.query.page) || 1);
const pageSize = ref(10);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const data = await apiGet(`/api/articles/?page=${page.value}`);
    articles.value = data.results || [];
    count.value = data.count || 0;
    if (data.page_size) pageSize.value = data.page_size;
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
  router.push({ query: { page: p } });
  load();
}

onMounted(() => {
  setSeo({
    title: siteStore.siteName || 'WhrBlog',
    description: siteStore.info?.SITE_SEO_DESCRIPTION,
    keywords: siteStore.info?.SITE_KEYWORDS,
    ogType: 'website',
  });
  load();
});

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
</script>

<template>
  <div class="space-y-5">
    <div v-if="loading" class="space-y-4">
      <div v-for="n in 3" :key="n" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5">
        <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded mb-3 w-2/3"></div>
        <div class="h-3 bg-gray-200 dark:bg-slate-700 rounded mb-2"></div>
        <div class="h-3 bg-gray-200 dark:bg-slate-700 rounded w-1/2"></div>
      </div>
    </div>
    <div v-else-if="error" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-red-500">加载失败：{{ error }}</div>
    <template v-else>
      <article v-for="a in articles" :key="a.id" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 hover:shadow-md transition">
        <h2 class="text-lg font-semibold mb-1">
          <router-link :to="a.url" class="text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400">
            {{ a.title }}
          </router-link>
          <span v-if="a.is_top" class="inline-block align-middle ml-2 px-1.5 py-0.5 rounded bg-amber-400/90 text-white text-xs font-medium">置顶</span>
        </h2>
        <div class="text-xs text-gray-400 mb-2 flex flex-wrap gap-2">
          <span>{{ a.author?.nickname || a.author?.username }}</span>
          <span>{{ formatDate(a.pub_time) }}</span>
          <span v-if="a.category">
            <router-link :to="a.category.url">{{ a.category.name }}</router-link>
          </span>
          <span>{{ a.views }} 阅读</span>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-300 line-clamp-3">{{ a.summary }}</p>
        <div class="mt-2 flex flex-wrap gap-1">
          <router-link v-for="t in a.tags" :key="t.id" :to="t.url"
            class="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400">
            #{{ t.name }}
          </router-link>
        </div>
      </article>

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