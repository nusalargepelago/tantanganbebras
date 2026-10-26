import type { RouteRecordRaw } from 'vue-router'

export const todosRoutes: RouteRecordRaw[] = [
  {
    path: '/todos',
    name: 'TodosList',
    component: () => import('./views/TodosPage.vue'),
    meta: {
      requiresAuth: true,
      title: 'Todos',
      description: 'Keep track of your tasks and reminders.',
    },
  },
]
