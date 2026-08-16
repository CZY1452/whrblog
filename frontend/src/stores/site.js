/**
 * 全局站点信息 store
 */
import { defineStore } from 'pinia';
import { apiGet } from '../api.js';

export const useSiteStore = defineStore('site', {
  state: () => ({
    info: null,
    loading: false,
  }),
  getters: {
    siteName: (s) => s.info?.SITE_NAME || 'WhrBlog',
    navCategories: (s) => s.info?.nav_category_list || [],
    navTags: (s) => s.info?.nav_tags || [],
    navPages: (s) => s.info?.nav_pages || [],
  },
  actions: {
    async load() {
      if (this.info || this.loading) return;
      this.loading = true;
      try {
        this.info = await apiGet('/api/siteinfo/');
      } catch (e) {
        console.error('siteinfo load failed:', e);
      } finally {
        this.loading = false;
      }
    },
  },
});