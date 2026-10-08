import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HousePricePredict from '@/views/HousePricePredict.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('@/views/AppLayout.vue'),
      meta: {requiresAuth: true},
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { requiresAuth: true, title: '仪表盘', affix: true, closable: false }
        },
        {
          path: 'analytics/price',
          name: 'AnalyticsPrice',
          component: () => import('@/views/AnalyticsPrice.vue'),
          meta: { requiresAuth: true, title: '价格分析' }
        },
        {
          path: 'analytics/type',
          name: 'AnalyticsType',
          component: () => import('@/views/AnalyticsType.vue'),
          meta: { requiresAuth: true, title: '户型与类别分析' }
        },
        {
          path: 'analytics/region',
          name: 'AnalyticsRegion',
          component: () => import('@/views/AnalyticsRegion.vue'),
          meta: { requiresAuth: true, title: '区域分析' }
        },
        {
          path: 'houses',
          name: 'Houses',
          // file is named `House.vue` in the repo (singular) — import correct file
          component: () => import('@/views/House.vue'),
          meta: {requiresAuth: true, title: '房源列表'}
        },
        {
          path: 'houses/:id',
          name: 'HouseDetail',
          component: () => import('@/views/HouseDetail.vue'),
          meta: {requiresAuth: true, title: '房源详情', activeMenu: '/houses'}
        },
        {
          path: 'collection',
          component: () => import('@/views/collection/CollectionLayout.vue'),
          meta: {requiresAuth: true, title: '推荐与收藏', activeMenu: '/collection/recommendations'},
          children: [
            {
              path: '',
              redirect: '/collection/recommendations'
            },
            {
              path: 'recommendations',
              name: 'HouseRecommendations',
              // actual file is `Recommendation.vue` (singular)
              component: () => import('@/views/collection/Recommendation.vue'),
              meta: {requiresAuth: true, title: '智能推荐', activeMenu: '/collection/recommendations'}
            },
            {
              path: 'favorites',
              name: 'Favorites',
              component: () => import('@/views/collection/Favorites.vue'),
              meta: {requiresAuth: true, title: '我的收藏', activeMenu: '/collection/favorites'}
            }
          ]
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('@/views/Profile.vue'),
          meta: { requiresAuth: true, title: '个人资料' }
        },
        {
          path: 'account/password',
          name: 'ChangePassword',
          component: () => import ('@/views/ChangePassword.vue'),
          meta: { requiresAuth: true, title: ' 修改密码 ', activeMenu: '/profile' }
        },
        {
          path: '/price-prediction',
          name: 'Predict',
          component: HousePricePredict,
          alias: ['/predict']
        },
        {
          path: 'assistant',
          name: 'Assistant',
          component: () => import ('@/views/AssistantChat.vue'),
          meta: { requiresAuth: true, title: ' 智能问答 ' }
        },
        {
          path: '/rag',
          name: 'rag',
          component: () => import('@/views/HouseRAG.vue'),
          meta: { requiresAuth: true, title: 'RAG问答' }
        },
        {
          path: '/admin/houses',
          name: 'AdminHouses',
          component: () => import('@/views/admin/HouseManage.vue'),
          meta: { title: '房源管理', requiresAdmin: true }
        }
      ]
    },
    {
      path: '/login',
      redirect: '/',
    },
    // legacy '/app' path used by login/register redirects -> send to dashboard
    {
      path: '/app',
      redirect: '/dashboard'
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue'),
      meta: { requiresAuth: false }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    // 已认证用户访问登录/注册页时，重定向到仪表盘
    next('/dashboard')
  } else if (to.meta.requiresAdmin && authStore.user?.user_type !== 'admin') {
    next('/login')
  } else {
    next()
  }
})

export default router