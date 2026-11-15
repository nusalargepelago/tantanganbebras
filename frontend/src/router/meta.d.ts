import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresStaff?: boolean
    requiresAdmin?: boolean
    allowTeacher?: boolean
    guestOnly?: boolean
    scroll?: boolean
    fullscreen?: boolean
    focusMode?: boolean
    title?: string
    description?: string
  }
}
