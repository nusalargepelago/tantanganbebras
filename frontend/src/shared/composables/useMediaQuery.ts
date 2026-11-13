import { onMounted, onUnmounted, ref, type Ref } from 'vue'

export function useMediaQuery(query: string): Ref<boolean> {
  const mql = window.matchMedia(query)
  const matches = ref(mql.matches)
  const onChange = (e: MediaQueryListEvent) => {
    matches.value = e.matches
  }
  onMounted(() => mql.addEventListener('change', onChange))
  onUnmounted(() => mql.removeEventListener('change', onChange))
  return matches
}
