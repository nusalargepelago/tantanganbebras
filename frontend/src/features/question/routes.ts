import type { RouteRecordRaw } from 'vue-router'

export const questionRoutes: RouteRecordRaw[] = [
  {
    path: '/question',
    name: 'QuestionList',
    component: () => import('./views/QuestionListPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Questions',
      description: 'Browse and manage the question bank.',
    },
  },
  {
    path: '/question/new',
    name: 'QuestionNew',
    component: () => import('./views/QuestionFormPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'New Question',
      description: 'Add a new question to the bank.',
    },
  },
  {
    path: '/question-editor',
    name: 'QuestionEditor',
    component: () => import('./views/QuestionEditorPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      scroll: false,
      title: 'Question Editor',
      description: 'Compose question content with the rich-text editor.',
    },
  },
  {
    path: '/question/:name',
    name: 'QuestionDetail',
    component: () => import('./views/QuestionDetailPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Question Detail',
      description: 'View the question prompt, answers, and metadata.',
    },
  },
  {
    path: '/question/:name/edit',
    name: 'QuestionEdit',
    component: () => import('./views/QuestionFormPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Edit Question',
      description: 'Edit this question.',
    },
  },
]
