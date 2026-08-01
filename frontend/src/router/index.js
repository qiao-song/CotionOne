import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/Home.vue'),
        meta: { title: 'Tbao - 商品广场' }
      },
      {
        path: 'my-shop',
        name: 'MyShop',
        component: () => import('../views/MyShop.vue'),
        meta: { title: '我的店铺', requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: '个人中心', requiresAuth: true }
      },
      {
        path: 'cart',
        name: 'Cart',
        component: () => import('../views/Cart.vue'),
        meta: { title: '购物车 - Tbao', requiresAuth: true }
      },
      {
        path: 'my-orders',
        name: 'MyOrders',
        component: () => import('../views/MyOrders.vue'),
        meta: { title: '我的订单 - Tbao', requiresAuth: true }
      },
      {
        path: 'goods/:id',
        name: 'ProductDetail',
        component: () => import('../views/ProductDetail.vue'),
        meta: { title: '商品详情 - Tbao' }
      },
      {
        path: 'discover',
        name: 'Discover',
        component: () => import('../views/Discover.vue'),
        meta: { title: '发现 - Tbao' }
      },
      {
        path: 'games',
        name: 'Games',
        component: () => import('../views/Games.vue'),
        meta: { title: '游戏中心 - Tbao', requiresAuth: true }
      },
      {
        path: 'seller/:id',
        name: 'SellerDetail',
        component: () => import('../views/SellerDetail.vue'),
        meta: { title: '卖家详情 - Tbao' }
      },
      {
        path: 'grass-square',
        name: 'GrassSquare',
        component: () => import('../views/GrassSquare.vue'),
        meta: { title: '种草广场 - Tbao' }
      },
      {
        path: 'post-editor',
        name: 'PostEditor',
        component: () => import('../views/PostEditor.vue'),
        meta: { title: '发布种草 - Tbao', requiresAuth: true }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录 - Tbao', guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { title: '注册 - Tbao', guest: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach(async (to, _from, next) => {
  document.title = to.meta.title || 'Tbao'

  const authStore = useAuthStore()

  // Only fetch user for routes that require auth (not for public or guest routes)
  if (to.meta.requiresAuth && !authStore.user && !authStore.loading) {
    await authStore.fetchUser()
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }

  if (to.meta.guest && authStore.isLoggedIn) {
    return next('/')
  }

  next()
})

export default router
