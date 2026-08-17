<script setup>
import { ref, onMounted } from 'vue';
import { apiGet, apiPost, apiPatch } from '../api.js';
import { setSeo } from '../seo.js';
import { useAuthStore } from '../stores/auth.js';
import PasswordInput from '../components/PasswordInput.vue';

const authStore = useAuthStore();

const user = ref(null);
const loading = ref(true);
const error = ref('');

// 资料编辑
const nickname = ref('');
const editingProfile = ref(false);
const savingProfile = ref(false);

// 修改密码
const oldPassword = ref('');
const newPassword = ref('');
const newPasswordConfirm = ref('');
const changingPassword = ref(false);

// 修改邮箱
const newEmail = ref('');
const changingEmail = ref(false);

// 头像
const avatarFile = ref(null);
const uploadingAvatar = ref(false);

const message = ref('');
const messageError = ref('');

function notifyOk(m) {
  message.value = m;
  messageError.value = '';
  setTimeout(() => (message.value = ''), 4000);
}
function notifyErr(m) {
  messageError.value = m;
  message.value = '';
}

async function load() {
  loading.value = true;
  error.value = '';
  try {
    user.value = await apiGet('/api/user');
    authStore.setUser(user.value);
    nickname.value = user.value.nickname || '';
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function saveProfile() {
  savingProfile.value = true;
  try {
    user.value = await apiPatch('/api/user', { nickname: nickname.value });
    authStore.setUser(user.value);
    notifyOk('资料已更新');
  } catch (e) {
    notifyErr(e.message);
  } finally {
    savingProfile.value = false;
  }
}

async function changePassword() {
  if (!oldPassword.value || !newPassword.value) return notifyErr('请填写完整信息');
  if (newPassword.value !== newPasswordConfirm.value) return notifyErr('两次输入的新密码不一致');
  changingPassword.value = true;
  try {
    const data = await apiPost('/api/change_password', {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    });
    oldPassword.value = '';
    newPassword.value = '';
    newPasswordConfirm.value = '';
    notifyOk(data.message || '密码修改成功');
  } catch (e) {
    notifyErr(e.message);
  } finally {
    changingPassword.value = false;
  }
}

async function changeEmail() {
  if (!newEmail.value.trim()) return notifyErr('请输入新邮箱');
  changingEmail.value = true;
  try {
    const data = await apiPost('/api/change_email', { new_email: newEmail.value });
    newEmail.value = '';
    notifyOk(data.message || '验证邮件已发送至新邮箱');
  } catch (e) {
    notifyErr(e.message);
  } finally {
    changingEmail.value = false;
  }
}

function onAvatarSelected(e) {
  const f = e.target.files && e.target.files[0];
  if (f) avatarFile.value = f;
}

async function uploadAvatar() {
  if (!avatarFile.value) return notifyErr('请选择头像文件');
  uploadingAvatar.value = true;
  try {
    const formData = new FormData();
    formData.append('avatar', avatarFile.value);
    const data = await apiPost('/api/upload_avatar', formData, true);
    user.value = { ...user.value, avatar: data.avatar };
    authStore.setUser(user.value);
    notifyOk('头像已更新');
  } catch (e) {
    notifyErr(e.message);
  } finally {
    uploadingAvatar.value = false;
    avatarFile.value = null;
  }
}

onMounted(() => {
  setSeo({ title: '个人中心 | WhrBlog', description: '管理个人资料、密码与邮箱。', ogType: 'website' });
  load();
});
</script>

<template>
  <div class="space-y-5">
    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
      <h1 class="text-xl font-bold mb-4">个人中心</h1>

      <p v-if="error" class="text-sm text-red-500 mb-3">{{ error }}</p>
      <p v-if="loading" class="text-sm text-gray-400">加载中…</p>

      <template v-else-if="user">
        <div v-if="message" class="mb-3 text-sm text-green-500">{{ message }}</div>
        <div v-if="messageError" class="mb-3 text-sm text-red-500">{{ messageError }}</div>

        <!-- 基本信息 -->
        <div class="flex items-center gap-4 mb-6">
          <img v-if="user.avatar" :src="user.avatar" alt="avatar" class="w-16 h-16 rounded-full object-cover" />
          <div v-else class="w-16 h-16 rounded-full bg-blue-500 text-white flex items-center justify-center text-2xl">
            {{ (user.nickname || user.username || '').charAt(0) }}
          </div>
          <div>
            <div class="font-semibold">{{ user.nickname || user.username }}</div>
            <div class="text-sm text-gray-500">@{{ user.username }}</div>
            <div class="text-sm text-gray-500">{{ user.email }}</div>
          </div>
        </div>

        <!-- 头像上传 -->
        <div class="border-t border-gray-100 dark:border-slate-700 pt-4 mb-4">
          <h3 class="font-semibold text-sm mb-2">更换头像</h3>
          <div class="flex items-center gap-2">
            <input type="file" accept="image/*" @change="onAvatarSelected" class="text-sm" />
            <button @click="uploadAvatar" :disabled="uploadingAvatar"
              class="px-4 py-2 rounded-lg text-sm bg-blue-600 text-white disabled:opacity-40">
              {{ uploadingAvatar ? '上传中…' : '上传' }}
            </button>
          </div>
        </div>

        <!-- 修改昵称 -->
        <div class="border-t border-gray-100 dark:border-slate-700 pt-4 mb-4">
          <h3 class="font-semibold text-sm mb-2">修改昵称</h3>
          <div class="flex items-center gap-2">
            <input v-model="nickname" type="text" class="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 p-2 text-sm bg-white dark:bg-slate-900" />
            <button @click="saveProfile" :disabled="savingProfile"
              class="px-4 py-2 rounded-lg text-sm bg-blue-600 text-white disabled:opacity-40">
              {{ savingProfile ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>

        <!-- 修改密码 -->
        <div class="border-t border-gray-100 dark:border-slate-700 pt-4 mb-4">
          <h3 class="font-semibold text-sm mb-2">修改密码</h3>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-2">
            <PasswordInput v-model="oldPassword" placeholder="原密码" />
            <PasswordInput v-model="newPassword" placeholder="新密码（至少8位）" :minlength="8" />
            <PasswordInput v-model="newPasswordConfirm" placeholder="确认新密码" :minlength="8" />
          </div>
          <button @click="changePassword" :disabled="changingPassword"
            class="px-4 py-2 rounded-lg text-sm bg-blue-600 text-white disabled:opacity-40">
            {{ changingPassword ? '提交中…' : '修改密码' }}
          </button>
        </div>

        <!-- 修改邮箱 -->
        <div class="border-t border-gray-100 dark:border-slate-700 pt-4 mb-4">
          <h3 class="font-semibold text-sm mb-2">修改邮箱（发送验证邮件至新邮箱）</h3>
          <div class="flex items-center gap-2">
            <input v-model="newEmail" type="email" placeholder="新邮箱地址" class="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 p-2 text-sm bg-white dark:bg-slate-900" />
            <button @click="changeEmail" :disabled="changingEmail"
              class="px-4 py-2 rounded-lg text-sm bg-blue-600 text-white disabled:opacity-40">
              {{ changingEmail ? '发送中…' : '发送验证邮件' }}
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>