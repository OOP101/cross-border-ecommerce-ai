import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'
import api, { ME_KEY, TOKEN_KEY } from '../api'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('../views/Chat.vue'),
        meta: { title: '智能客服', icon: 'ChatDotRound' },
      },
      {
        path: 'copywriting',
        name: 'Copywriting',
        component: () => import('../views/Copywriting.vue'),
        meta: { title: '智能文案', icon: 'EditPen' },
      },
      {
        path: 'translation',
        name: 'Translation',
        component: () => import('../views/Translation.vue'),
        meta: { title: '翻译引擎', icon: 'Switch' },
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/Knowledge.vue'),
        meta: { title: '知识库管理', icon: 'Collection' },
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('../views/Analytics.vue'),
        meta: { title: '数据洞察', icon: 'DataAnalysis' },
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('../views/Admin.vue'),
        meta: { title: '管理后台', icon: 'Setting' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 守卫为无状态判断：本地已有当前用户（me）即放行，否则调 /auth/me 校验。
// 演示模式（AUTH_REQUIRED=false）即使无令牌也会返回默认主体，正常进入；
// 登录过期时由 axios 拦截器清除凭据并踢回登录页。
router.beforeEach(async (to) => {
  if (to.name === 'Login') return true
  if (localStorage.getItem(ME_KEY)) return true
  try {
    const me = await api.get('/auth/me', { __silent: true })
    localStorage.setItem(ME_KEY, JSON.stringify(me))
    return true
  } catch (e) {
    return { name: 'Login' }
  }
})

router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} · 国际贸易智能平台` : '国际贸易智能平台'
})

export default router
