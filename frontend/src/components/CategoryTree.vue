<script setup>
defineProps({
  categories: { type: Array, default: () => [] },
  depth: { type: Number, default: 1 },
});

const MAX_DEPTH = 4;
</script>

<template>
  <div v-if="categories.length" class="space-y-2">
    <div v-for="c in categories" :key="c.id" class="rounded-lg p-3 border border-gray-200 dark:border-slate-700 hover:border-blue-400 hover:shadow transition">
      <router-link :to="c.url" class="flex items-center gap-3 group">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-amber-500 shrink-0" fill="currentColor" viewBox="0 0 24 24">
          <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
        </svg>
        <div class="min-w-0">
          <div class="text-sm font-medium truncate text-gray-800 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400">{{ c.name }}</div>
          <div class="text-xs text-gray-400">{{ c.article_count }} 篇</div>
        </div>
      </router-link>
      <div v-if="depth < MAX_DEPTH && c.child_categories?.length" class="mt-2 ml-4 pl-3 border-l border-gray-200 dark:border-slate-700">
        <CategoryTree :categories="c.child_categories" :depth="depth + 1" />
      </div>
    </div>
  </div>
</template>