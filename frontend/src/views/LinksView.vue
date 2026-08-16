<script setup>
import { ref, onMounted } from 'vue';
import { apiGet } from '../api.js';
import { setSeo } from '../seo.js';

const links = ref([]);
const loading = ref(true);
const error = ref(null);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const data = await apiGet('/api/links/');
    links.value = Array.isArray(data) ? data : (data?.results || []);
    setSeo({
      title: '友情链接 | WhrBlog',
      description: '本站友情链接列表。',
      ogType: 'website',
    });
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="space-y-5">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-5">
      <h1 class="text-xl font-bold">友情链接</h1>
    </div>

    <div v-if="loading" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-gray-400">加载中…</div>
    <div v-else-if="error" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-red-500">{{ error }}</div>
    <div v-else-if="!links.length" class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 text-sm text-gray-400">暂无友链</div>

    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
      <a v-for="l in links" :key="l.id" :href="l.link" target="_blank" rel="noopener"
        class="flex items-center justify-between gap-2 p-3 rounded-lg border border-gray-100 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 transition">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-200">{{ l.name }}</span>
        <span class="text-xs text-gray-400 truncate">{{ l.link }}</span>
      </a>
    </div>
  </div>
</template>