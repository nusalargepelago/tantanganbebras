import type { RouteRecordRaw } from 'vue-router'

export const practiceRoutes: RouteRecordRaw[] = [
  {
    path: '/student/practice',
    name: 'PracticeList',
    component: () => import('./views/PracticeListPage.vue'),
    meta: {
      requiresAuth: true,
      title: 'Practice',
      description: 'Practice questions for your category.',
    },
  },
  {
    path: '/practice',
    name: 'PracticeAdminList',
    component: () => import('./views/PracticeAdminListPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Practice Review',
      description: 'Review practice sheets submitted by students.',
    },
  },
  {
    path: '/practice/:name',
    name: 'PracticeAdminDetail',
    component: () => import('./views/PracticeAdminDetailPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Practice Detail',
      description: 'Compare a practice sheet before and after shuffling.',
    },
  },
  {
    path: '/student/practice/start',
    name: 'PracticeRunner',
    component: () => import('./views/PracticeRunnerPage.vue'),
    meta: {
      requiresAuth: true,
      scroll: false,
      focusMode: true,
      title: 'Practice',
      description: 'Answer the questions in your practice sheet.',
    },
  },
  {
    path: '/student/practice/:name',
    name: 'PracticeResult',
    component: () => import('./views/PracticeResultPage.vue'),
    meta: {
      requiresAuth: true,
      title: 'Practice Result',
      description: 'See your practice score and answer review.',
    },
  },
]
