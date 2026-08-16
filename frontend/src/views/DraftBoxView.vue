<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { apiGet, apiPost, apiDelete, apiDownloadFile } from '../api.js';
import { setSeo } from '../seo.js';
import { useAuthStore } from '../stores/auth.js';

const router = useRouter();
const authStore = useAuthStore();

const drafts = ref([]);
const loading = ref(true);
const error = ref('');
const message = ref('');
const actionId = ref(null);

const isSuperuser = ref(authStore.isSuperuser);

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const data = await apiGet('/api/drafts/');
    drafts.value = data.results || data || [];
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function editDraft(id) {
  router.push(`/write?id=${id}`);
}

async function publishDraft(id) {
  if (!confirm('确定要发布这篇草稿吗？')) return;
  actionId.value = id;
  message.value = '';
  error.value = '';
  try {
    await apiPost(`/api/drafts/${id}/publish/`, {});
    message.value = '文章已发布！';
    drafts.value = drafts.value.filter(d => d.id !== id);
  } catch (e) {
    error.value = e.message;
  } finally {
    actionId.value = null;
  }
}

async function deleteDraft(id) {
  if (!confirm('确定要删除这篇草稿吗？此操作不可恢复。')) return;
  actionId.value = id;
  message.value = '';
  error.value = '';
  try {
    await apiDelete(`/api/drafts/${id}/`);
    message.value = '草稿已删除。';
    drafts.value = drafts.value.filter(d => d.id !== id);
  } catch (e) {
    error.value = e.message;
  } finally {
    actionId.value = null;
  }
}

async function exportDraft(id) {
  actionId.value = id;
  error.value = '';
  try {
    await apiDownloadFile(`/api/articles/${id}/export/`);
  } catch (e) {
    error.value = '导出失败：' + e.message;
  } finally {
    actionId.value = null;
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

onMounted(() => {
  setSeo({ title: '草稿箱 | WhrBlog', description: '管理博客草稿文章。', ogType: 'website' });
  load();
});
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 md:p-8">
      <div class="flex items-center justify-between mb-5">
        <h1 class="text-xl font-bold">草稿箱</h1>
        <router-link to="/write"
          class="px-4 py-2 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700">
          写新文章
        </router-link>
      </div>

      <p v-if="!isSuperuser" class="text-sm text-red-500">仅管理员可以访问此页面。</p>

      <template v-else>
        <div v-if="message" class="mb-3 text-sm text-green-500">{{ message }}</div>
        <div v-if="error" class="mb-3 text-sm text-red-500">{{ error }}</div>

        <div v-if="loading" class="space-y-4">
          <div v-for="n in 3" :key="n" class="border border-gray-100 dark:border-slate-700 rounded-lg p-4">
            <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded mb-2 w-1/2"></div>
            <div class="h-3 bg-gray-200 dark:bg-slate-700 rounded w-1/3"></div>
          </div>
        </div>

        <div v-else-if="drafts.length === 0" class="text-center py-12 text-gray-400">
          <p class="text-lg mb-2">暂无草稿</p>
          <p class="text-sm">点击「写新文章」开始创作吧</p>
        </div>

        <div v-else class="space-y-3">
          <div v-for="d in drafts" :key="d.id"
            class="border border-gray-100 dark:border-slate-700 rounded-lg p-4 hover:shadow transition">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-gray-900 dark:text-white truncate">{{ d.title }}</h3>
                <div class="text-xs text-gray-400 mt-1 flex flex-wrap gap-2">
                  <span v-if="d.category">{{ d.category.name }}</span>
                  <span>创建于 {{ formatDate(d.creation_time) }}</span>
                  <span>修改于 {{ formatDate(d.last_modify_time) }}</span>
                </div>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <button @click="exportDraft(d.id)" :disabled="actionId === d.id"
                  class="px-3 py-1.5 rounded text-xs border border-gray-200 dark:border-slate-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 disabled:opacity-40">
                  导出
                </button>
                <button @click="editDraft(d.id)"
                  class="px-3 py-1.5 rounded text-xs border border-gray-200 dark:border-slate-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700">
                  编辑
                </button>
                <button @click="publishDraft(d.id)" :disabled="actionId === d.id"
                  class="px-3 py-1.5 rounded text-xs text-white bg-green-600 hover:bg-green-700 disabled:opacity-40">
                  发布
                </button>
                <button @click="deleteDraft(d.id)" :disabled="actionId === d.id"
                  class="px-3 py-1.5 rounded text-xs text-white bg-red-500 hover:bg-red-600 disabled:opacity-40">
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
