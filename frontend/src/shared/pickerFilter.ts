/**
 * Pure helpers for option pickers — no imports, so they can run under plain
 * node for smoke checks.
 *
 * `masterListEmpty` mirrors frappe-ui's `matchesByLabelOrValue`
 * (`shared/selection/utils.ts`): lowercase substring match on `label` or
 * `value`, empty query matches everything. Keep semantics identical so the
 * "empty list" condition of a creatable row always agrees with what the
 * Combobox would render.
 */
export interface PickerOption {
  label: string
  value: string | number
}

/** True when no option matches `query` (empty query ⇒ empty options). */
export function masterListEmpty(
  options: PickerOption[],
  query: string,
): boolean {
  const q = query.toLowerCase()
  if (!q) return options.length === 0
  return !options.some(
    (o) =>
      o.label.toLowerCase().includes(q) ||
      String(o.value).toLowerCase().includes(q),
  )
}
