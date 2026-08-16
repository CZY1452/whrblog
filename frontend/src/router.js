/**
 * Vue Router - SPA 路由表
 */
import { createRouter, createWebHistory } from 'vue-router';

import HomeView from './views/HomeView.vue';
import ArticleDetailView from './views/ArticleDetailView.vue';
import CategoryView from './views/CategoryView.vue';
import TagView from './views/TagView.vue';
import AuthorView from './views/AuthorView.vue';
import LinksView from './views/LinksView.vue';
import SearchView from './views/SearchView.vue';
import LoginView from './views/LoginView.vue';
import RegisterView from './views/RegisterView.vue';
import ForgetPasswordView from './views/ForgetPasswordView.vue';
import UserCenterView from './views/UserCenterView.vue';
import VerifyEmailView from './views/VerifyEmailView.vue';
import ArticleEditorView from './views/ArticleEditorView.vue';
import DraftBoxView from './views/DraftBoxView.vue';

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/article/:id', name: 'article', component: ArticleDetailView },
  { path: '/category/:slug', name: 'category', component: CategoryView },
  { path: '/tag/:slug', name: 'tag', component: TagView },
  { path: '/author/:name', name: 'author', component: AuthorView },
  { path: '/links', name: 'links', component: LinksView },
  { path: '/search', name: 'search', component: SearchView },
  { path: '/login', name: 'login', component: LoginView, meta: { hideSidebar: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { hideSidebar: true } },
  { path: '/forget-password', name: 'forget-password', component: ForgetPasswordView, meta: { hideSidebar: true } },
  { path: '/user', name: 'user', component: UserCenterView, meta: { hideSidebar: true } },
  { path: '/write', name: 'write', component: ArticleEditorView, meta: { hideSidebar: true } },
  { path: '/drafts', name: 'drafts', component: DraftBoxView, meta: { hideSidebar: true } },
  { path: '/verify-email', name: 'verify-email', component: VerifyEmailView, meta: { hideSidebar: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
