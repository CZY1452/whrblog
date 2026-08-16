<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { apiPost } from '../api.js';
import { setSeo } from '../seo.js';

const route = useRoute();
const id = route.query.id;
const sign = route.query.sign;

const loading = ref(true);
const message = ref('');
const success = ref(false);

onMounted(async () => {
  setSeo({ title: '邮箱验证 | WhrBlog', description: '验证邮箱完成账号激活。', ogType: 'website' });
  try {
    const data = await apiPost('/api/verify_email', { id: id, sign: sign });
    success.value = true;
    message.value = data.message || '邮箱验证成功';
  } catch (e) {
    success.value = false;
    message.value = e.message;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="max-w-md mx-auto">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-6 md:p-8 text-center">
      <div v-if="loading" class="text-sm text-gray-400 py-6">验证中…</div>
      <template v-else>
        <div :class="success ? 'text-green-500' : 'text-red-500'" class="text-lg font-semibold mb-2">
          {{ success ? '✓' : '✗' }}
        </div>
        <p :class="success ? 'text-green-600 dark:text-green-400' : 'text-red-500'" class="mb-6">{{ message }}</p>
        <router-link v-if="success" to="/login" class="inline-block px-5 py-2.5 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700">
          去登录
        </router-link>
        <router-link v-else to="/" class="inline-block px-5 py-2.5 rounded-lg text-sm text-white bg-gray-600 hover:bg-gray-700">
          返回首页
        </router-link>
      </template>
    </div>
  </div>
</template>