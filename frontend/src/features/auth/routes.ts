import type { RouteRecordRaw } from 'vue-router'

export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/LoginView.vue'),
    meta: {
      guestOnly: true,
      title: 'Sign in',
      description: 'Sign in to your account.',
    },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('./views/RegisterView.vue'),
    meta: {
      guestOnly: true,
      title: 'Create account',
      description: 'Create an account to get started.',
    },
  },
  {
    path: '/student-login',
    name: 'StudentLogin',
    component: () => import('./views/StudentLoginView.vue'),
    meta: {
      guestOnly: true,
      title: 'Student Sign in',
      description: 'Sign in with your student account.',
    },
  },
  {
    path: '/student-register',
    name: 'StudentRegister',
    component: () => import('./views/StudentRegisterView.vue'),
    meta: {
      guestOnly: true,
      title: 'Student Registration',
      description: 'Register as a student to join challenges and practice.',
    },
  },
]
