<script setup>
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useSiteStore } from '../stores/site.js';
import { useAuthStore } from '../stores/auth.js';
import { apiPost } from '../api.js';

const route = useRoute();
const siteStore = useSiteStore();
const authStore = useAuthStore();
const mobileOpen = ref(false);

const siteName = computed(() => siteStore.siteName);
const navCategories = computed(() => siteStore.navCategories);
const navTags = computed(() => siteStore.navTags);
const navPages = computed(() => siteStore.navPages);
const user = computed(() => authStore.user);
const isSuperuser = computed(() => authStore.isSuperuser);

const avatarText = computed(() => {
  if (!user.value) return '';
  const name = user.value.nickname || user.value.username || '';
  return name.charAt(0);
});

const userAvatar = computed(() => user.value?.avatar || '');

function isActive(path) {
  return route.path === path;
}

async function logout() {
  try {
    await apiPost('/api/logout', {});
  } catch (e) { /* ignore */ }
  authStore.clear();
  window.location.href = '/';
}
</script>

<template>
  <header class="bg-white dark:bg-slate-800 shadow sticky top-0 z-50">
    <div class="container mx-auto px-4 lg:px-8 max-w-6xl h-16 flex items-center justify-between">
      <router-link to="/" class="flex items-center gap-2 text-xl font-bold text-gray-900 dark:text-white">
        <span class="text-blue-600 dark:text-blue-400">◆</span>
        {{ siteName }}
      </router-link>

      <nav class="hidden lg:flex items-center gap-1">
        <router-link to="/" class="px-3 py-2 rounded text-sm hover:bg-gray-100 dark:hover:bg-slate-700"
          :class="isActive('/') ? 'text-blue-600 dark:text-blue-400 font-medium' : ''">首页</router-link>
        <div class="relative group">
          <span class="px-3 py-2 rounded text-sm cursor-pointer inline-flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-slate-700"
            :class="route.path.startsWith('/category') ? 'text-blue-600 dark:text-blue-400 font-medium' : ''">
            分类
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </span>
          <div class="absolute left-0 top-full w-56 hidden group-hover:block bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-100 dark:border-slate-700 py-1 z-50">
            <router-link v-for="c in navCategories" :key="c.id" :to="c.url"
              class="block px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-slate-700 text-gray-700 dark:text-gray-200">
              {{ c.name }}
              <span class="text-xs text-gray-400 ml-2">{{ c.article_count }} 篇</span>
            </router-link>
          </div>
        </div>
        <div class="relative group" v-if="navTags.length">
          <span class="px-3 py-2 rounded text-sm cursor-pointer inline-flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-slate-700"
            :class="route.path.startsWith('/tag') ? 'text-blue-600 dark:text-blue-400 font-medium' : ''">
            标签
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </span>
          <div class="absolute left-0 top-full w-56 hidden group-hover:block bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-100 dark:border-slate-700 py-1 z-50">
            <router-link v-for="t in navTags" :key="t.id" :to="t.url"
              class="block px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-slate-700 text-gray-700 dark:text-gray-200">
              {{ t.name }}
              <span class="text-xs text-gray-400 ml-2">{{ t.article_count }} 篇</span>
            </router-link>
          </div>
        </div>
        <router-link to="/links" class="px-3 py-2 rounded text-sm hover:bg-gray-100 dark:hover:bg-slate-700"
          :class="isActive('/links') ? 'text-blue-600 dark:text-blue-400 font-medium' : ''">友链</router-link>
        <router-link to="/search" class="px-3 py-2 rounded text-sm hover:bg-gray-100 dark:hover:bg-slate-700"
          :class="isActive('/search') ? 'text-blue-600 dark:text-blue-400 font-medium' : ''">搜索</router-link>
      </nav>

      <div class="flex items-center gap-2">
        <template v-if="user">
          <router-link to="/user" class="flex items-center gap-2">
            <img v-if="userAvatar" :src="userAvatar" alt="avatar" class="w-8 h-8 rounded-full object-cover" />
            <span v-else class="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm">
              {{ avatarText }}
            </span>
            <span class="hidden sm:inline text-sm">{{ user.nickname || user.username }}</span>
          </router-link>
          <router-link v-if="isSuperuser" to="/write" class="px-3 py-2 rounded text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700">写文章</router-link>
          <router-link v-if="isSuperuser" to="/drafts" class="px-3 py-2 rounded text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700">草稿箱</router-link>
          <a v-if="isSuperuser" href="/admin/" class="px-3 py-2 rounded text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700">管理后台</a>
          <button @click="logout" class="px-3 py-2 rounded text-sm hover:bg-gray-100 dark:hover:bg-slate-700">退出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="px-3 py-2 rounded text-sm text-blue-600 dark:text-blue-400 hover:bg-gray-100 dark:hover:bg-slate-700">登录</router-link>
          <router-link to="/register" class="px-3 py-2 rounded text-sm bg-blue-600 text-white hover:bg-blue-700">注册</router-link>
        </template>
        <button @click="mobileOpen = !mobileOpen" class="lg:hidden px-2 py-2 text-gray-600 dark:text-gray-300">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
    </div>

    <nav v-if="mobileOpen" class="lg:hidden border-t border-gray-100 dark:border-slate-700 px-4 py-2 flex flex-col">
      <router-link to="/" class="py-2 text-sm">首页</router-link>
      <router-link v-for="c in navCategories" :key="c.id" :to="c.url" class="py-2 text-sm">
        分类 · {{ c.name }} <span class="text-xs text-gray-400">({{ c.article_count }} 篇)</span>
      </router-link>
      <router-link v-for="t in navTags" :key="t.id" :to="t.url" class="py-2 text-sm">
        标签 · {{ t.name }} <span class="text-xs text-gray-400">({{ t.article_count }} 篇)</span>
      </router-link>
      <router-link to="/links" class="py-2 text-sm">友链</router-link>
      <router-link to="/search" class="py-2 text-sm">搜索</router-link>
    </nav>
  </header>
</template>
