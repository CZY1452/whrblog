<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { apiGet } from '../api.js';

const route = useRoute();
const data = ref(null);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  await load();
});

watch(() => route.params.id, async () => {
  await load();
});

async function load() {
  loading.value = true;
  error.value = null;
  try {
    let url = '/api/sidebar/?linktype=p';
    if (route.params.id) url += `&article_id=${encodeURIComponent(route.params.id)}`;
    data.value = await apiGet(url);
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

const recent = computed(() => data.value?.recent_articles || []);
const mostRead = computed(() => data.value?.most_read_articles || []);
const categories = computed(() => data.value?.sidebar_categorys || []);
const tags = computed(() => data.value?.sidebar_tags || []);
const extraSidebars = computed(() => data.value?.extra_sidebars || []);
</script>

<template>
  <aside class="space-y-6">
    <div v-if="loading" class="space-y-4">
      <div class="h-5 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
      <div class="h-20 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
    </div>
    <div v-else-if="error" class="text-sm text-red-500">加载失败：{{ error }}</div>
    <template v-else>
      <div v-for="sb in extraSidebars" :key="'sb-' + sb.id" class="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
        <h3 class="text-sm font-semibold mb-2 text-gray-800 dark:text-gray-200">{{ sb.name }}</h3>
        <div class="text-sm prose dark:prose-invert" v-html="sb.content_html"></div>
      </div>

      <div v-if="recent.length" class="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
        <h3 class="text-sm font-semibold mb-3 text-gray-800 dark:text-gray-200">最新文章</h3>
        <ul class="space-y-2">
          <li v-for="a in recent" :key="a.id">
            <router-link :to="a.url" class="text-sm text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
              {{ a.title }}
            </router-link>
            <span class="block text-xs text-gray-400">{{ formatDate(a.pub_time) }}</span>
          </li>
        </ul>
      </div>

      <div v-if="mostRead.length" class="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
        <h3 class="text-sm font-semibold mb-3 text-gray-800 dark:text-gray-200">阅读排行</h3>
        <ul class="space-y-2">
          <li v-for="a in mostRead" :key="a.id">
            <router-link :to="a.url" class="text-sm text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
              {{ a.title }}
            </router-link>
            <span class="block text-xs text-gray-400">{{ a.views }} 次阅读</span>
          </li>
        </ul>
      </div>

      <div v-if="categories.length" class="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
        <h3 class="text-sm font-semibold mb-3 text-gray-800 dark:text-gray-200">分类</h3>
        <ul class="space-y-1">
          <li v-for="c in categories" :key="c.id">
            <router-link :to="c.url" class="text-sm text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
              {{ c.name }}（{{ c.article_count }}）
            </router-link>
          </li>
        </ul>
      </div>

      <div v-if="tags.length" class="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
        <h3 class="text-sm font-semibold mb-3 text-gray-800 dark:text-gray-200">标签云</h3>
        <div class="flex flex-wrap gap-2">
          <router-link v-for="t in tags" :key="t.id" :to="t.url"
            class="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900"
            :style="{ fontSize: t.size + 'px' }">
            {{ t.name }}
          </router-link>
        </div>
      </div>
    </template>
  </aside>
</template>