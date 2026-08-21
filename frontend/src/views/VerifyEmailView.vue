<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiPost } from '../api.js';
import { setSeo } from '../seo.js';

const route = useRoute();
const router = useRouter();
const userId = route.query.id;

const code = ref('');
const loading = ref(false);
const message = ref('');
const success = ref(false);
const resending = ref(false);
const resendMsg = ref('');

onMounted(() => {
  setSeo({ title: '邮箱验证 | WhrBlog', description: '输入验证码完成账号激活。', ogType: 'website' });
});

async function submit() {
  if (!code.value.trim() || code.value.trim().length !== 6) {
    message.value = '请输入 6 位验证码';
    return;
  }
  loading.value = true;
  message.value = '';
  success.value = false;
  try {
    const data = await apiPost('/api/verify_email', { id: userId, code: code.value.trim() });
    success.value = true;
    message.value = data.message || '邮箱验证成功';
  } catch (e) {
    success.value = false;
    message.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function resend() {
  resending.value = true;
  resendMsg.value = '';
  try {
    const data = await apiPost('/api/resend_verify_email', { id: userId });
    resendMsg.value = data.message || '验证码已重新发送';
  } catch (e) {
    resendMsg.value = e.message;
  } finally {
    resending.value = false;
  }
}
</script>

<template>
  <div class="max-w-md mx-auto">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-6 md:p-8 text-center">
      <h1 class="text-xl font-bold mb-2">邮箱验证</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        我们已向您的邮箱发送 6 位验证码（1 分钟内有效），请输入完成账号激活。
      </p>

      <form @submit.prevent="submit" class="space-y-4">
        <input
          v-model="code"
          type="text"
          inputmode="numeric"
          autocomplete="one-time-code"
          maxlength="6"
          placeholder="6 位验证码"
          class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-center text-2xl tracking-[0.5em] bg-white dark:bg-slate-900"
        />

        <p v-if="message" :class="success ? 'text-green-600 dark:text-green-400' : 'text-red-500'" class="text-sm">
          {{ message }}
        </p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 font-medium"
        >
          {{ loading ? '验证中…' : '验证' }}
        </button>
      </form>

      <div class="mt-4">
        <button
          type="button"
          :disabled="resending"
          @click="resend"
          class="text-sm text-blue-600 dark:text-blue-400 hover:underline disabled:opacity-40"
        >
          {{ resending ? '发送中…' : '重新发送验证码' }}
        </button>
        <p v-if="resendMsg" class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ resendMsg }}</p>
      </div>

      <router-link
        v-if="success"
        to="/login"
        class="inline-block mt-6 px-5 py-2.5 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700"
      >
        去登录
      </router-link>
    </div>
  </div>
</template>
