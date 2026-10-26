import type { RouteRecordRaw } from 'vue-router'

export const studentRoutes: RouteRecordRaw[] = [
  {
    path: '/student',
    name: 'StudentList',
    component: () => import('./views/StudentListPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Students',
      description: 'Browse and manage student accounts.',
    },
  },
  {
    path: '/student/import',
    name: 'StudentImport',
    component: () => import('./views/StudentImportPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Import Students',
      description: 'Import students in bulk from a CSV file.',
    },
  },
  {
    path: '/student/new',
    name: 'StudentNew',
    component: () => import('./views/StudentFormPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'New Student',
      description: 'Create a new student account.',
    },
  },
  {
    path: '/student/:userId',
    name: 'StudentDetail',
    component: () => import('./views/StudentDetailPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Student Detail',
      description: "View a student's profile, school, and status.",
    },
  },
  {
    path: '/student/:userId/edit',
    name: 'StudentEdit',
    component: () => import('./views/StudentFormPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Edit Student',
      description: 'Edit this student profile.',
    },
  },
]
