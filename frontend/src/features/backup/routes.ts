import type { RouteRecordRaw } from 'vue-router'

export const backupRoutes: RouteRecordRaw[] = [
  {
    path: '/backup',
    name: 'Backup',
    component: () => import('./views/BackupPage.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Backup & Restore',
      description: 'Export the whole database or restore it from a previous backup.',
    },
  },
]
