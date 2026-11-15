import type { RouteRecordRaw } from 'vue-router'

export const schoolRoutes: RouteRecordRaw[] = [
  {
    path: 'schools',
    name: 'Schools',
    component: () => import('./views/SchoolListView.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Schools',
      description: 'Manage the canonical school list.',
    },
  },
]
