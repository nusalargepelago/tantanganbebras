import type { RouteRecordRaw } from 'vue-router'

export const onboardingRoutes: RouteRecordRaw[] = [
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('./views/OnboardingView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Choose your role',
      description: 'Choose whether you join as a student or a teacher.',
    },
  },
]
