<script setup>
import { ref, onMounted } from 'vue';
import { apiPost } from '../api.js';
import { setSeo } from '../seo.js';
import PasswordInput from '../components/PasswordInput.vue';

const email = ref('');
const password = ref('');
const passwordConfirm = ref('');
const code = ref('');
const loading = ref(false);
const sendingCode = ref(false);
const error = ref('');
const success = ref('');
const codeSent = ref(false);

async function sendCode() {
  if (!email.value.trim()) {
    error.value = '请先填写邮箱';
    return;
  }
  sendingCode.value = true;
  error.value = '';
  try {
    const data = await apiPost('/api/forget_password_code', { email: email.value });
    codeSent.value = true;
    success.value = data.message || '验证码已发送';
  } catch (e) {
    error.value = e.message;
  } finally {
    sendingCode.value = false;
  }
}

async function submit() {
  if (!email.value.trim() || !password.value) {
    error.value = '请填写完整信息';
    return;
  }
  if (password.value !== passwordConfirm.value) {
    error.value = '两次输入的密码不一致';
    return;
  }
  if (password.value.length < 8) {
    error.value = '密码至少 8 位';
    return;
  }
  loading.value = true;
  error.value = '';
  try {
    const data = await apiPost('/api/forget_password', {
      email: email.value,
      code: code.value,
      new_password: password.value,
      new_password_confirm: passwordConfirm.value,
    });
    success.value = data.message || '密码重置成功，请使用新密码登录';
    email.value = '';
    password.value = '';
    passwordConfirm.value = '';
    code.value = '';
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  setSeo({ title: '找回密码 | WhrBlog', description: '重置 WhrBlog 账号密码。', ogType: 'website' });
});
</script>

<template>
  <div class="max-w-md mx-auto">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-6 md:p-8">
      <h1 class="text-xl font-bold text-center mb-6">找回密码</h1>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">注册邮箱</label>
          <div class="flex gap-2">
            <input v-model="email" type="email" required class="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900" />
            <button type="button" @click="sendCode" :disabled="sendingCode"
              class="px-4 py-2 rounded-lg text-xs bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600 disabled:opacity-40 whitespace-nowrap">
              {{ sendingCode ? '发送中…' : (codeSent ? '重新发送' : '获取验证码') }}
            </button>
          </div>
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">邮箱验证码</label>
          <input v-model="code" type="text" class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900" />
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">新密码</label>
          <PasswordInput v-model="password" required :minlength="8" placeholder="请输入新密码" />
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">确认新密码</label>
          <PasswordInput v-model="passwordConfirm" required :minlength="8" placeholder="请再次输入新密码" />
        </div>

        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        <p v-if="success" class="text-sm text-green-500">{{ success }}</p>

        <button type="submit" :disabled="loading"
          class="w-full py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 font-medium">
          {{ loading ? '提交中…' : '重置密码' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-gray-500">
        想起密码了？<router-link to="/login" class="text-blue-600 dark:text-blue-400 hover:underline">去登录</router-link>
      </p>
    </div>
  </div>
</template>