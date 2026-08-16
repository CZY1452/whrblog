<script setup>
import { ref, onMounted } from 'vue';
import { apiPost } from '../api.js';
import { setSeo } from '../seo.js';
import { useAuthStore } from '../stores/auth.js';
import PasswordInput from '../components/PasswordInput.vue';

const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const remember = ref(true);
const loading = ref(false);
const error = ref('');

async function submit() {
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码';
    return;
  }
  loading.value = true;
  error.value = '';
  try {
    const data = await apiPost('/api/login', { username: username.value, password: password.value, remember: remember.value });
    authStore.setUser(data.user);
    window.location.href = '/';
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  setSeo({ title: '登录 | WhrBlog', description: '登录 WhrBlog 账号。', ogType: 'website' });
});
</script>

<template>
  <div class="max-w-md mx-auto">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-6 md:p-8">
      <h1 class="text-xl font-bold text-center mb-6">登录</h1>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">用户名</label>
          <input v-model="username" type="text" required class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900" />
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">密码</label>
          <PasswordInput v-model="password" required placeholder="请输入密码" />
        </div>
        <div class="flex items-center justify-between text-sm">
          <label class="flex items-center gap-2 text-gray-600 dark:text-gray-300">
            <input v-model="remember" type="checkbox" class="rounded" /> 两周内自动登录
          </label>
          <router-link to="/forget-password" class="text-blue-600 dark:text-blue-400 hover:underline">忘记密码？</router-link>
        </div>

        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

        <button type="submit" :disabled="loading"
          class="w-full py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 font-medium">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-gray-500">
        还没有账号？<router-link to="/register" class="text-blue-600 dark:text-blue-400 hover:underline">立即注册</router-link>
      </p>
    </div>
  </div>
</template>