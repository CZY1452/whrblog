<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { apiGet } from '../api.js';
import { setSeo } from '../seo.js';

const route = useRoute();
const slug = () => route.params.slug;

const meta = ref(null);
const articles = ref([]);
const loading = ref(true);
const error = ref(null);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [t, list] = await Promise.all([
      apiGet(`/api/tags/${slug()}/`),
      apiGet(`/api/articles/?tag=${encodeURIComponent(slug())}`),
    ]);
    meta.value = t;
    articles.value = list.results || [];
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

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

watch(() => route.params.slug, load);
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
        </h2>
        <div class="text-xs text-gray-400 mt-1">{{ a.author?.nickname || a.author?.username }} · {{ formatDate(a.pub_time) }} · {{ a.views }} 阅读</div>
        <p class="text-sm text-gray-600 dark:text-gray-300 mt-2">{{ a.summary }}</p>
      </div>
    </template>
  </div>
</template>