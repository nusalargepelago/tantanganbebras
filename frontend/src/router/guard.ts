import { useAuthStore } from '@/features/auth/store'
import { useSetupStore } from '@/features/setup/store'

export async function authGuard(to: any) {
  const setup = useSetupStore()
  if (setup.status === null && !setup.statusFailed) {
    await setup.fetchStatus()
  }
  if (setup.status?.setupRequired) {
    return to.path === '/setup' ? true : '/setup'
  }
  if (to.path === '/setup') {
    return '/'
  }

  const auth = useAuthStore()
  if (!auth.checked) {
    await auth.fetchMe()
  }
  if (to.meta.requiresAuth && !auth.user && !auth.student) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'Onboarding' && (!auth.user || auth.isAdmin)) {
    return '/'
  }
  if (to.meta.requiresAuth && auth.user && !auth.isAdmin) {
    if (auth.classification === null) {
      await auth.fetchClassification()
    }
    if (auth.classification === 'none' && to.name !== 'Onboarding') {
      return { name: 'Onboarding' }
    }
    if (auth.classification !== 'none' && to.name === 'Onboarding') {
      return '/'
    }
  }
  if (
    to.meta.requiresStaff &&
    !auth.isAdmin &&
    (auth.isStudent || (auth.isTeacher && !to.meta.allowTeacher))
  ) {
    return '/'
  }
  if (to.meta.requiresAdmin && auth.user?.appRole !== 'admin') {
    return '/'
  }
  if (to.meta.guestOnly) {
    if (auth.user || auth.student) return '/'
    await auth.fetchRegistrationMode()
    if (to.name === 'Register' && auth.registrationMode === 'closed') {
      return { path: '/login' }
    }
  }
  return true
}
