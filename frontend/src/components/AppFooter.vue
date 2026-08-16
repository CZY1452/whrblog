<script setup>
import { computed } from 'vue';
import { useSiteStore } from '../stores/site.js';

const siteStore = useSiteStore();
const year = new Date().getFullYear();
const siteName = computed(() => siteStore.siteName);
const info = computed(() => siteStore.info);
</script>

<template>
  <footer class="mt-12 border-t border-gray-100 dark:border-slate-800">
    <div class="container mx-auto px-4 lg:px-8 max-w-6xl py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-gray-400">
      <div>© {{ year }} {{ siteName }}</div>
      <div class="flex gap-4">
        <span v-if="info?.BEIAN_CODE">{{ info.BEIAN_CODE }}</span>
        <span v-if="info?.SHOW_GONGAN_CODE && info?.BEIAN_CODE_GONGAN">{{ info.BEIAN_CODE_GONGAN }}</span>
      </div>
    </div>
  </footer>
</template>
