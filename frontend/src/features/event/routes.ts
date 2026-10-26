import type { RouteRecordRaw } from 'vue-router'

export const eventRoutes: RouteRecordRaw[] = [
  {
    path: '/event',
    name: 'EventList',
    component: () => import('./views/EventListPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Events',
      description: 'Browse and manage challenges.',
    },
  },
  {
    path: '/event/new',
    name: 'EventNew',
    component: () => import('./views/EventFormPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'New Event',
      description: 'Create a new challenge.',
    },
  },
  {
    path: '/event/:name/results',
    name: 'EventResults',
    component: () => import('./views/EventResultsPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Event Results',
      description: 'View participant results for this challenge.',
    },
  },
  {
    path: '/event/:name/edit',
    name: 'EventEdit',
    component: () => import('./views/EventFormPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Edit Event',
      description: 'Edit this challenge.',
    },
  },
  {
    path: '/event/:name',
    name: 'EventDetail',
    component: () => import('./views/EventDetailPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      title: 'Event Detail',
      description: 'View the challenge details and its questions.',
    },
  },
]
