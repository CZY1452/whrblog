<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiGet } from '../api.js';
import { setSeo } from '../seo.js';
import CategoryTree from '../components/CategoryTree.vue';

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
    const [c, list] = await Promise.all([
      apiGet(`/api/categories/${slug()}/`),
      apiGet(`/api/articles/?category=${encodeURIComponent(slug())}&page=${page.value}`),
    ]);
    meta.value = c;
    articles.value = list.results || [];
    count.value = list.count || 0;
    if (list.page_size) pageSize.value = list.page_size;
    setSeo({
      title: c.seo_title,
      description: c.seo_description,
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

const childCats = computed(() => meta.value?.child_categories || []);

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
      <div class="text-xs text-gray-400 mb-1"><router-link to="/" class="hover:text-blue-600">首页</router-link> / 分类 / {{ meta?.name }}</div>
      <h1 class="text-xl font-bold">分类：{{ meta?.name }}</h1>
      <p class="text-sm text-gray-500 mt-1">{{ meta?.seo_description }}</p>
    </div>

    <div v-if="loading" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-gray-400">加载中…</div>
    <div v-else-if="error" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-red-500">{{ error }}</div>
    <template v-else>
      <div v-if="childCats.length" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5">
        <h2 class="text-sm font-semibold text-gray-500 mb-3">子目录</h2>
        <CategoryTree :categories="childCats" :depth="1" />
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-5">
        <h2 class="text-sm font-semibold text-gray-500 mb-3">文章<span v-if="childCats.length" class="text-gray-400">（本目录直属）</span></h2>
        <template v-if="!articles.length">
          <p class="text-sm text-gray-400">该分类下暂无文章</p>
        </template>
        <template v-else>
          <div v-for="a in articles" :key="a.id" class="py-3 first:pt-0 last:pb-0 border-b border-gray-100 dark:border-slate-700 last:border-0">
            <h2 class="text-lg font-semibold">
              <router-link :to="a.url" class="hover:text-blue-600 dark:hover:text-blue-400">{{ a.title }}</router-link>
              <span v-if="a.is_top" class="inline-block align-middle ml-2 px-1.5 py-0.5 rounded bg-amber-400/90 text-white text-xs font-medium">置顶</span>
            </h2>
            <div class="text-xs text-gray-400 mt-1">{{ a.author?.nickname || a.author?.username }} · {{ formatDate(a.pub_time) }} · {{ a.views }} 阅读</div>
            <p class="text-sm text-gray-600 dark:text-gray-300 mt-2">{{ a.summary }}</p>
          </div>
        </template>
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