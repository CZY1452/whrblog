<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { apiGet, apiPost, apiPatch, getCsrfToken } from '../api.js';
import { setSeo } from '../seo.js';
import { useAuthStore } from '../stores/auth.js';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const categories = ref([]);
const tags = ref([]);

const title = ref('');
const body = ref('');
const category = ref('');
const selectedTags = ref([]);
const status = ref('p');
const commentStatus = ref('o');
const saving = ref(false);
const loading = ref(false);
const error = ref('');
const message = ref('');
const importing = ref(false);
const fileInput = ref(null);

const isSuperuser = computed(() => authStore.isSuperuser);
const editingId = ref(null);
const isEditing = computed(() => !!editingId.value);

async function loadOptions() {
  try {
    const [catRes, tagRes] = await Promise.all([
      apiGet('/api/categories/'),
      apiGet('/api/tags/'),
    ]);
    categories.value = Array.isArray(catRes) ? catRes : catRes.results || [];
    tags.value = Array.isArray(tagRes) ? tagRes : tagRes.results || [];
  } catch (e) {
    error.value = e.message;
  }
}

async function loadDraft(id) {
  loading.value = true;
  error.value = '';
  try {
    const data = await apiGet(`/api/drafts/${id}/`);
    title.value = data.title || '';
    body.value = data.body || '';
    category.value = data.category || '';
    selectedTags.value = data.tags || [];
    status.value = data.status || 'd';
    commentStatus.value = data.comment_status || 'o';
    editingId.value = id;
  } catch (e) {
    error.value = '加载草稿失败：' + e.message;
  } finally {
    loading.value = false;
  }
}

function toggleTag(id) {
  const idx = selectedTags.value.indexOf(id);
  if (idx >= 0) selectedTags.value.splice(idx, 1);
  else selectedTags.value.push(id);
}

function triggerImport() {
  if (fileInput.value) fileInput.value.click();
}

async function importMarkdown(event) {
  const file = event.target.files[0];
  if (!file) return;
  event.target.value = '';
  importing.value = true;
  error.value = '';
  message.value = '';
  try {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/articles/import/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrfToken() },
      credentials: 'same-origin',
      body: formData,
    });
    const payload = await res.json().catch(() => null);
    if (!res.ok || !payload) {
      const msg = payload?.detail || `服务器返回 ${res.status}`;
      throw new Error(msg);
    }
    title.value = payload.title || title.value;
    body.value = payload.body || body.value;
    if (payload.category) {
      const match = categories.value.find(c => c.name === payload.category);
      if (match) category.value = match.id;
    }
    if (payload.tags && payload.tags.length) {
      const tagIds = [];
      for (const name of payload.tags) {
        const match = tags.value.find(t => t.name === name);
        if (match) tagIds.push(match.id);
      }
      if (tagIds.length) selectedTags.value = tagIds;
    }
    message.value = '文件已导入，请检查内容后保存。';
  } catch (e) {
    error.value = '导入失败：' + e.message;
  } finally {
    importing.value = false;
  }
}

async function submit() {
  if (!title.value.trim()) {
    error.value = '请输入文章标题';
    return;
  }
  if (!body.value.trim()) {
    error.value = '请输入文章内容';
    return;
  }
  if (!category.value) {
    error.value = '请选择文章分类';
    return;
  }
  saving.value = true;
  error.value = '';
  message.value = '';

  const payload = {
    title: title.value.trim(),
    body: body.value,
    category: category.value,
    tags: selectedTags.value,
    status: status.value,
    comment_status: commentStatus.value,
  };

  try {
    let data;
    if (isEditing.value) {
      data = await apiPatch(`/api/drafts/${editingId.value}/`, payload);
      message.value = '文章已更新！';
    } else {
      data = await apiPost('/api/article_create', payload);
      message.value = '文章已保存！';
    }

    if (status.value === 'p' && !isEditing.value) {
      router.push(`/article/${data.id}`);
    } else if (status.value === 'p' && isEditing.value) {
      router.push(`/article/${editingId.value}`);
    } else {
      // 保存为草稿：新建模式清空表单，编辑模式保留
      if (!isEditing.value) {
        title.value = '';
        body.value = '';
        selectedTags.value = [];
      }
    }
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  const draftId = route.query.id;
  if (draftId) {
    setSeo({ title: '编辑文章 | WhrBlog', description: '编辑博客文章草稿。', ogType: 'website' });
    await loadOptions();
    await loadDraft(draftId);
  } else {
    setSeo({ title: '发表文章 | WhrBlog', description: '撰写并发布新的博客文章。', ogType: 'website' });
    await loadOptions();
    if (categories.value.length) category.value = categories.value[0].id;
  }
});
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-5 md:p-8">
      <div class="flex items-center justify-between mb-5">
        <h1 class="text-xl font-bold">{{ isEditing ? '编辑文章' : '发表文章' }}</h1>
        <div class="flex items-center gap-3">
          <button @click="triggerImport" :disabled="importing"
            class="px-3 py-1.5 rounded text-sm border border-gray-200 dark:border-slate-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 disabled:opacity-40">
            {{ importing ? '导入中…' : '导入 .md' }}
          </button>
          <input ref="fileInput" type="file" accept=".md" class="hidden" @change="importMarkdown" />
          <router-link v-if="isEditing" to="/drafts"
            class="text-sm text-gray-500 hover:text-blue-600 dark:hover:text-blue-400">
            &larr; 返回草稿箱
          </router-link>
        </div>
      </div>

      <p v-if="!isSuperuser" class="text-sm text-red-500 mb-4">仅管理员可以访问此页面。</p>

      <template v-else>
        <div v-if="loading" class="text-center py-12 text-gray-400">加载中…</div>

        <template v-else>
          <div v-if="message" class="mb-3 text-sm text-green-500">{{ message }}</div>
          <div v-if="error" class="mb-3 text-sm text-red-500">{{ error }}</div>

          <div class="space-y-4">
            <div>
              <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">标题</label>
              <input v-model="title" type="text" placeholder="文章标题"
                class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900" />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">分类</label>
                <select v-model="category"
                  class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900">
                  <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">状态</label>
                <select v-model="status"
                  class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900">
                  <option value="p">发布</option>
                  <option value="d">草稿</option>
                </select>
              </div>
              <div>
                <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">评论</label>
                <select v-model="commentStatus"
                  class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900">
                  <option value="o">开放</option>
                  <option value="c">关闭</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">标签</label>
              <div class="flex flex-wrap gap-2">
                <button v-for="t in tags" :key="t.id" @click="toggleTag(t.id)" type="button"
                  class="px-3 py-1 rounded text-xs border"
                  :class="selectedTags.includes(t.id)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-200 dark:border-slate-700 text-gray-600 dark:text-gray-300'">
                  {{ t.name }}
                </button>
              </div>
            </div>

            <div>
              <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">正文（Markdown）</label>
              <textarea v-model="body" rows="16" placeholder="使用 Markdown 编写文章内容…"
                class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900 font-mono"></textarea>
            </div>

            <button @click="submit" :disabled="saving"
              class="w-full py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 font-medium">
              {{ saving ? '保存中…' : (isEditing ? '保存修改' : (status === 'p' ? '发布' : '保存草稿')) }}
            </button>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
