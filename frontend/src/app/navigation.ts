import type { RouteDestination } from 'frappe-ui'

export interface NavItem {
  key: string
  labelKey: string
  mobileLabelKey?: string
  icon: string
  route: RouteDestination
  requireAdmin?: boolean
  mobile?: boolean
}

export interface MenuPreference {
  order: string[]
  hidden: string[]
}

const NAV_ITEMS: NavItem[] = [
  {
    key: 'Dashboard',
    labelKey: 'nav.dashboard',
    mobileLabelKey: 'nav.home',
    icon: 'lucide-house',
    route: { name: 'Dashboard' },
  },
  {
    key: 'Users',
    labelKey: 'nav.users',
    icon: 'lucide-users',
    route: { name: 'Users' },
    requireAdmin: true,
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

const MAX_MOBILE_NAV_ITEMS = 3

export function mobileNavItems(items: NavItem[]): NavItem[] {
  return items.filter((item) => item.mobile !== false).slice(0, MAX_MOBILE_NAV_ITEMS)
}

export function visibleNavItems(order: string[], hidden: string[]): NavItem[] {
  const hiddenKeys = new Set(hidden)
  return orderedNavItems(order).filter((item) => !hiddenKeys.has(item.key))
}
