import type { RouteRecordRaw } from 'vue-router'

export const eventStudentRoutes: RouteRecordRaw[] = [
  {
    path: '/student/event',
    name: 'EventStudentList',
    component: () => import('./views/EventStudentListPage.vue'),
    meta: {
      requiresAuth: true,
      title: 'Challenges',
      description: 'Browse available challenges and your attempts.',
    },
  },
  {
    path: '/student/event/start/:name',
    name: 'EventStudentRunner',
    component: () => import('./views/EventStudentRunnerPage.vue'),
    meta: {
      requiresAuth: true,
      scroll: false,
      focusMode: true,
      title: 'Challenge',
      description: 'Answer the questions in this challenge.',
    },
  },
  {
    path: '/student/event/result/:name',
    name: 'EventStudentResult',
    component: () => import('./views/EventStudentResultPage.vue'),
    meta: {
      requiresAuth: true,
      title: 'Challenge Result',
      description: 'See your challenge score and answer review.',
    },
  },
]
