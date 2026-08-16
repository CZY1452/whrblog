<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useSiteStore } from './stores/site.js';
import { useAuthStore } from './stores/auth.js';
import AppHeader from './components/AppHeader.vue';
import AppSidebar from './components/AppSidebar.vue';
import AppFooter from './components/AppFooter.vue';

const route = useRoute();
const siteStore = useSiteStore();
const authStore = useAuthStore();

onMounted(() => {
  siteStore.load();
  authStore.load();
});
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100">
    <AppHeader />
    <div class="container mx-auto px-4 lg:px-8 max-w-6xl flex flex-col lg:flex-row gap-6 mt-6">
      <main class="flex-1 min-w-0">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </main>
      <AppSidebar v-if="!route.meta.hideSidebar" class="lg:w-72 w-full shrink-0" />
    </div>
    <AppFooter />
  </div>
</template>
