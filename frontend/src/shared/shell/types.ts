import type { RouteDestination } from 'frappe-ui'

/**
 * One navigation row as the shell components consume it. Labels arrive
 * already resolved (the shell does not know about i18n) and `active` is
 * computed by the host, because matching rules are app-specific.
 */
export interface ShellNavItem {
  key: string
  label: string
  icon: string
  route: RouteDestination
  active?: boolean
}
