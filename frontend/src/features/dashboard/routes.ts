import type { RouteRecordRaw } from 'vue-router'

export const dashboardRoutes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'Dashboard',
    component: () => import('./views/HomeView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Home',
      description: 'Quick links to your practice, challenges, and account pages.',
    },
  },
  {
    path: '/dashboard',
    name: 'AdminDashboard',
    component: () => import('./views/AdminDashboardView.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Dashboard',
      description: 'Overview of events, students, and platform statistics.',
    },
  },
  {
    path: '/student/dashboard',
    name: 'StudentDashboard',
    component: () => import('./views/StudentDashboardView.vue'),
    meta: {
      requiresAuth: true,
      title: 'My Dashboard',
      description: 'Your practice and challenge activity at a glance.',
    },
  },
]
