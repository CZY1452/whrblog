/**
 * 当前登录用户状态 store
 */
import { defineStore } from 'pinia';
import { apiGet } from '../api.js';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loaded: false,
  }),
  getters: {
    isAuthenticated: (s) => !!s.user,
    isSuperuser: (s) => !!(s.user && s.user.is_superuser),
  },
  actions: {
    async load() {
      if (this.loaded) return;
      try {
        this.user = await apiGet('/api/user');
      } catch (e) {
        this.user = null;
      } finally {
        this.loaded = true;
      }
    },
    setUser(u) {
      this.user = u;
      this.loaded = true;
    },
    clear() {
      this.user = null;
      this.loaded = true;
    },
  },
});