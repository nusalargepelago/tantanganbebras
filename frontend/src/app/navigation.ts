import type { RouteDestination } from 'frappe-ui'

export type NavRole = 'staff' | 'student' | 'admin'

export interface NavRoleFlags {
  staff: boolean
  student: boolean
  admin: boolean
}

export interface NavItem {
  key: string
  labelKey: string
  icon: string
  route: RouteDestination
  match: string[]
  roles?: NavRole[]
  primary?: boolean
}

const NESTED_NAMESPACES: Record<string, string[]> = {
  '/student': ['/student/dashboard', '/student/event', '/student/practice'],
}

export const NAV_ITEMS: NavItem[] = [
  {
    key: 'home',
    labelKey: 'nav.home',
    icon: 'lucide-house',
    route: { name: 'Dashboard' },
    match: ['/'],
    primary: true,
  },
  {
    key: 'adminDashboard',
    labelKey: 'nav.dashboard',
    icon: 'lucide-layout-dashboard',
    route: { name: 'AdminDashboard' },
    match: ['/dashboard'],
    roles: ['staff'],
    primary: true,
  },
  {
    key: 'studentDashboard',
    labelKey: 'nav.dashboard',
    icon: 'lucide-layout-dashboard',
    route: { name: 'StudentDashboard' },
    match: ['/student/dashboard'],
    roles: ['student'],
    primary: true,
  },
  {
    key: 'practice',
    labelKey: 'nav.practice',
    icon: 'lucide-clipboard-list',
    route: { name: 'PracticeList' },
    match: ['/student/practice'],
    roles: ['student'],
    primary: true,
  },
  {
    key: 'events',
    labelKey: 'nav.events',
    icon: 'lucide-calendar',
    route: { name: 'EventStudentList' },
    match: ['/student/event'],
    roles: ['student'],
  },
  {
    key: 'questionBank',
    labelKey: 'nav.questionBank',
    icon: 'lucide-library',
    route: { name: 'QuestionList' },
    match: ['/question'],
    roles: ['staff'],
    primary: true,
  },
  {
    key: 'event',
    labelKey: 'nav.event',
    icon: 'lucide-calendar',
    route: { name: 'EventList' },
    match: ['/event', '/student/event'],
    roles: ['staff'],
  },
  {
    key: 'students',
    labelKey: 'nav.students',
    icon: 'lucide-users',
    route: { name: 'StudentList' },
    match: ['/student'],
    roles: ['staff'],
  },
  {
    key: 'practiceReview',
    labelKey: 'nav.practiceReview',
    icon: 'lucide-clipboard-check',
    route: { name: 'PracticeAdminList' },
    match: ['/practice'],
    roles: ['staff'],
  },
  {
    key: 'todos',
    labelKey: 'nav.todo',
    icon: 'lucide-list-todo',
    route: { name: 'TodosList' },
    match: ['/todos'],
    roles: ['staff'],
  },
  {
    key: 'users',
    labelKey: 'nav.users',
    icon: 'lucide-user-cog',
    route: { name: 'UsersList' },
    match: ['/users'],
    roles: ['admin'],
  },
  {
    key: 'backup',
    labelKey: 'nav.backup',
    icon: 'lucide-database',
    route: { name: 'Backup' },
    match: ['/backup'],
    roles: ['admin'],
  },
]

function matchesPrefix(prefix: string, path: string): boolean {
  if (prefix === '/') return path === '/'
  return (
    path === prefix || path.startsWith(`${prefix}/`) || path.startsWith(`${prefix}-`)
  )
}

function inNestedNamespace(prefix: string, path: string): boolean {
  return (NESTED_NAMESPACES[prefix] ?? []).some(
    (ns) => path === ns || path.startsWith(`${ns}/`),
  )
}

export function isNavActive(item: NavItem, path: string): boolean {
  return item.match.some(
    (prefix) => matchesPrefix(prefix, path) && !inNestedNamespace(prefix, path),
  )
}

export function navFor(flags: NavRoleFlags): NavItem[] {
  return NAV_ITEMS.filter(
    (item) => !item.roles || item.roles.some((role) => flags[role]),
  )
}

/**
 * The tabs that fit the mobile bottom bar: Home, Dashboard, one primary section
 * (the avatar tab makes four). An admin who also owns a student profile resolves
 * both staff and student primaries, so the duplicate Dashboard label collapses and
 * the list is capped — everything cut here stays reachable in the menu sheet.
 */
export function primaryNav(flags: NavRoleFlags): NavItem[] {
  const seen = new Set<string>()
  const primary = navFor(flags).filter((item) => {
    if (!item.primary || seen.has(item.labelKey)) return false
    seen.add(item.labelKey)
    return true
  })
  return primary.slice(0, 3)
}
