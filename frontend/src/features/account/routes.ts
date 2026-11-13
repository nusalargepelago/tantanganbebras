import type { RouteRecordRaw } from 'vue-router'

export const accountRoutes: RouteRecordRaw[] = [
  {
    path: '/users',
    name: 'Users',
    component: () => import('./views/UsersView.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Users',
      description: 'Administer user accounts: role, status, and group memberships.',
    },
  },
]
