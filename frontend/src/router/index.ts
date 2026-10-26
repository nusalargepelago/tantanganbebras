import { watch } from 'vue'
import {
  createRouter,
  createWebHistory,
  type RouteLocationNormalized,
  type RouteRecordRaw,
} from 'vue-router'

import { i18n } from '@/app/i18n'
import AppShell from '@/app/AppShell.vue'
import { onTourRouteChange } from '@/app/tour/store'
import { authRoutes } from '@/features/auth/routes'
import { useAuthStore } from '@/features/auth/store'
import { backupRoutes } from '@/features/backup/routes'
import { dashboardRoutes } from '@/features/dashboard/routes'
import { eventRoutes } from '@/features/event/routes'
import { eventStudentRoutes } from '@/features/event-student/routes'
import { practiceRoutes } from '@/features/practice/routes'
import { questionRoutes } from '@/features/question/routes'
import { setupRoutes } from '@/features/setup/routes'
import { studentRoutes } from '@/features/student/routes'
import { todosRoutes } from '@/features/todos/routes'
import { usersRoutes } from '@/features/users/routes'
import { brand } from '@/shared/brand'
import { authGuard } from './guard'

const routes: RouteRecordRaw[] = [
  ...authRoutes,
  ...setupRoutes,
  {
    path: '/',
    component: AppShell,
    children: [
      ...dashboardRoutes,
      ...backupRoutes,
      ...questionRoutes,
      ...studentRoutes,
      ...usersRoutes,
      ...practiceRoutes,
      ...eventRoutes,
      ...eventStudentRoutes,
      ...todosRoutes,
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(authGuard)

const { t, te } = i18n.global

function applyHead(to: RouteLocationNormalized) {
  const titleKey = `route.${String(to.name)}.title`
  const title = te(titleKey) ? t(titleKey) : to.meta.title
  document.title = title ? `${title} · ${brand.name}` : brand.name

  const descriptionKey = `route.${String(to.name)}.description`
  const description =
    (te(descriptionKey) ? t(descriptionKey) : to.meta.description) ||
    brand.description
  let meta = document.querySelector<HTMLMetaElement>('meta[name="description"]')
  if (description) {
    if (!meta) {
      meta = document.createElement('meta')
      meta.name = 'description'
      document.head.appendChild(meta)
    }
    meta.content = description
  } else {
    meta?.remove()
  }
}

router.afterEach((to) => {
  applyHead(to)
  onTourRouteChange(to.name ? String(to.name) : null)
})

watch(i18n.global.locale, () => applyHead(router.currentRoute.value))

window.addEventListener('auth:unauthorized', () => {
  const auth = useAuthStore()
  auth.user = null
  auth.student = null
  auth.checked = true
  const current = router.currentRoute.value
  if (current.matched.length > 0 && current.meta.requiresAuth) {
    router.replace({ path: '/login', query: { redirect: current.fullPath } })
  }
})

export default router
