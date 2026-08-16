/**
 * WhrBlog 前端 - Vue 3 SPA 入口
 */
import { createApp } from 'vue';
import { createPinia } from 'pinia';

import './styles/main.css';
import App from './App.vue';
import router from './router';

import { initDarkMode } from './features/darkMode.js';

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount('#app');

initDarkMode();