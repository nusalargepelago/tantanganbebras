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
  mobileLabelKey?: string
  icon: string
  route: RouteDestination
  roles?: NavRole[]
  mobile?: boolean
}

export interface MenuPreference {
  order: string[]
  hidden: string[]
}

export const NAV_ITEMS: NavItem[] = [
  {
    key: 'Dashboard',
    labelKey: 'nav.home',
    mobileLabelKey: 'nav.home',
    icon: 'lucide-house',
    route: { name: 'Dashboard' },
  },
  {
    key: 'PracticeList',
    labelKey: 'nav.practice',
    icon: 'lucide-clipboard-list',
    route: { name: 'PracticeList' },
    roles: ['student'],
  },
  {
    key: 'EventStudentList',
    labelKey: 'nav.events',
    icon: 'lucide-calendar',
    route: { name: 'EventStudentList' },
    roles: ['student'],
  },
  {
    key: 'QuestionList',
    labelKey: 'nav.questionBank',
    icon: 'lucide-library',
    route: { name: 'QuestionList' },
    roles: ['staff'],
  },
  {
    key: 'EventList',
    labelKey: 'nav.event',
    icon: 'lucide-calendar',
    route: { name: 'EventList' },
    roles: ['staff'],
  },
  {
    key: 'StudentList',
    labelKey: 'nav.students',
    icon: 'lucide-users',
    route: { name: 'StudentList' },
    roles: ['staff'],
  },
  {
    key: 'PracticeAdminList',
    labelKey: 'nav.practiceReview',
    icon: 'lucide-clipboard-check',
    route: { name: 'PracticeAdminList' },
    roles: ['staff'],
  },
  {
    key: 'TodosList',
    labelKey: 'nav.todo',
    icon: 'lucide-list-todo',
    route: { name: 'TodosList' },
    roles: ['staff'],
  },
  {
    key: 'Users',
    labelKey: 'nav.users',
    icon: 'lucide-user-cog',
    route: { name: 'Users' },
    roles: ['admin'],
  },
  {
    key: 'Backup',
    labelKey: 'nav.backup',
    icon: 'lucide-database',
    route: { name: 'Backup' },
    roles: ['admin'],
  },
  {
    key: 'Schools',
    labelKey: 'nav.schools',
    icon: 'lucide-school',
    route: { name: 'Schools' },
    roles: ['admin'],
  },
]

export function orderedNavItems(order: string[]): NavItem[] {
  const remaining = new Map(NAV_ITEMS.map((item) => [item.key, item]))
  const ordered: NavItem[] = []

  for (const key of order) {
    const item = remaining.get(key)
    if (!item) continue
    ordered.push(item)
    remaining.delete(key)
  }

  for (const item of NAV_ITEMS) {
    if (remaining.has(item.key)) ordered.push(item)
  }

  return ordered
}

export function visibleNavItems(order: string[], hidden: string[]): NavItem[] {
  const hiddenKeys = new Set(hidden)
  return orderedNavItems(order).filter((item) => !hiddenKeys.has(item.key))
}

export const MAX_MOBILE_NAV_ITEMS = 3

export function mobileNavItems(items: NavItem[]): NavItem[] {
  return items.filter((item) => item.mobile !== false).slice(0, MAX_MOBILE_NAV_ITEMS)
}
