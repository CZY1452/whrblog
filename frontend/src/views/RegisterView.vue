<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { apiPost } from '../api.js';
import { setSeo } from '../seo.js';
import PasswordInput from '../components/PasswordInput.vue';

const router = useRouter();

const username = ref('');
const email = ref('');
const code = ref('');
const nickname = ref('');
const password = ref('');
const passwordConfirm = ref('');
const loading = ref(false);
const error = ref('');
const success = ref('');
const sendMsg = ref('');
const cooling = ref(false);
const countdown = ref(60);
let timer = null;

const emailValid = computed(() =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())
);

async function sendCode() {
  if (!emailValid.value) {
    sendMsg.value = '请先填写正确的邮箱';
    return;
  }
  cooling.value = true;
  sendMsg.value = '';
  try {
    const data = await apiPost('/api/send_register_code', { email: email.value.trim() });
    sendMsg.value = data.message || '验证码已发送';
    countdown.value = 60;
    timer = setInterval(() => {
      countdown.value -= 1;
      if (countdown.value <= 0) {
        clearInterval(timer);
        cooling.value = false;
      }
    }, 1000);
  } catch (e) {
    sendMsg.value = e.message;
    cooling.value = false;
    // 被限流且能解析出等待时长时，进入冷却倒计时，避免反复点击
    if (e.status === 429 && e.wait && e.wait <= 600) {
      cooling.value = true;
      countdown.value = e.wait;
      timer = setInterval(() => {
        countdown.value -= 1;
        if (countdown.value <= 0) {
          clearInterval(timer);
          cooling.value = false;
        }
      }, 1000);
    }
  }
}

async function submit() {
  if (!username.value.trim() || !email.value.trim() || !password.value || !code.value.trim()) {
    error.value = '请填写完整信息（含邮箱验证码）';
    return;
  }
  if (password.value !== passwordConfirm.value) {
    error.value = '两次输入的密码不一致';
    return;
  }
  loading.value = true;
  error.value = '';
  success.value = '';
  try {
    const data = await apiPost('/api/register', {
      username: username.value,
      email: email.value,
      nickname: nickname.value,
      password: password.value,
      password_confirm: passwordConfirm.value,
      code: code.value.trim(),
    });
    success.value = data.message || '注册成功';
    router.push('/login');
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  setSeo({ title: '注册 | WhrBlog', description: '注册 WhrBlog 账号。', ogType: 'website' });
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<template>
  <div class="max-w-md mx-auto">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-6 md:p-8">
      <h1 class="text-xl font-bold text-center mb-6">注册</h1>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">用户名 *</label>
          <input v-model="username" type="text" required class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900" />
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">邮箱 *</label>
          <div class="flex gap-2">
            <input v-model="email" type="email" required class="flex-1 min-w-0 rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900" />
            <button
              type="button"
              :disabled="cooling || !emailValid"
              @click="sendCode"
              class="shrink-0 px-3 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 whitespace-nowrap"
            >
              {{ cooling ? countdown + 's' : '发送验证码' }}
            </button>
          </div>
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">验证码 *（邮箱收到的 6 位数字，1 分钟内有效）</label>
          <input v-model="code" type="text" inputmode="numeric" maxlength="6" placeholder="6 位验证码" class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm text-center tracking-[0.5em] bg-white dark:bg-slate-900" />
          <p v-if="sendMsg" class="text-xs text-green-600 dark:text-green-400 mt-1">{{ sendMsg }}</p>
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">昵称</label>
          <input v-model="nickname" type="text" class="w-full rounded-lg border border-gray-200 dark:border-slate-700 p-3 text-sm bg-white dark:bg-slate-900" />
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">密码 *（至少 8 位）</label>
          <PasswordInput v-model="password" required :minlength="8" placeholder="请输入密码" />
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-600 dark:text-gray-300">确认密码 *</label>
          <PasswordInput v-model="passwordConfirm" required :minlength="8" placeholder="请再次输入密码" />
        </div>

        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        <p v-if="success" class="text-sm text-green-500">{{ success }}</p>

        <button type="submit" :disabled="loading"
          class="w-full py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 font-medium">
          {{ loading ? '注册中…' : '注册' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-gray-500">
        已有账号？<router-link to="/login" class="text-blue-600 dark:text-blue-400 hover:underline">去登录</router-link>
      </p>
    </div>
  </div>
</template>
