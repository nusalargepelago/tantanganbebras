import { onScopeDispose, ref, watch } from 'vue'

export interface ListControlsOptions {
  fetch: (query: { search: string; perPage: number }) => Promise<unknown>
  setPage: (page: number) => void
  initialSearch?: string
  initialPerPage?: number
}

export function useListControls(options: ListControlsOptions) {
  const search = ref(options.initialSearch ?? '')
  const perPage = ref(options.initialPerPage ?? 20)

  let searchTimer: ReturnType<typeof setTimeout> | null = null

  function reload() {
    return options.fetch({ search: search.value, perPage: perPage.value })
  }

  watch(search, () => {
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      options.setPage(1)
      reload()
    }, 300)
  })

  watch(perPage, () => {
    options.setPage(1)
    reload()
  })

  function goToPage(page: number) {
    options.setPage(page)
    reload()
  }

  onScopeDispose(() => {
    if (searchTimer) clearTimeout(searchTimer)
  })

  return { search, perPage, reload, goToPage }
}
