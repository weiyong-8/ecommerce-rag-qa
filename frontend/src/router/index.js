import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  { path: '/', name: 'chat', component: () => import('../views/ChatView.vue') },
  {
    path: '/admin',
    name: 'admin-kb',
    component: () => import('../views/admin/KnowledgeBaseView.vue'),
    meta: { requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 登录态与管理员角色守卫(后端接口已做二次校验,前端守卫只负责体验)
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.path === '/login') {
    return token ? '/' : true
  }
  if (!token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && localStorage.getItem('role') !== 'admin') {
    return { path: '/' }
  }
  return true
})

export default router
