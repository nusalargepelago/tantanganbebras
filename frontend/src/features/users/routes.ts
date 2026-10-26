import type { RouteRecordRaw } from 'vue-router'

export const usersRoutes: RouteRecordRaw[] = [
  {
    path: '/users',
    name: 'UsersList',
    component: () => import('./views/UserListPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      requiresAdmin: true,
      title: 'Users',
      description: 'Manage user accounts and roles.',
    },
  },
  {
    path: '/users/new',
    name: 'UserNew',
    component: () => import('./views/UserFormPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      requiresAdmin: true,
      title: 'New User',
      description: 'Create a new user account.',
    },
  },
  {
    path: '/users/:id',
    name: 'UserDetail',
    component: () => import('./views/UserDetailPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      requiresAdmin: true,
      title: 'User Detail',
      description: 'View user details, roles, and access.',
    },
  },
  {
    path: '/users/:id/edit',
    name: 'UserEdit',
    component: () => import('./views/UserFormPage.vue'),
    meta: {
      requiresAuth: true,
      requiresStaff: true,
      requiresAdmin: true,
      title: 'Edit User',
      description: 'Edit this user account.',
    },
  },
]
