import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const dismissed = ref(false)

export function useFocusMode() {
  const route = useRoute()

  watch(
    () => route.meta.focusMode,
    (enabled) => {
      if (enabled) dismissed.value = false
    },
  )

  const active = computed(
    () => route.meta.focusMode === true && !dismissed.value,
  )

  function toggle() {
    dismissed.value = !dismissed.value
  }

  return { active, toggle }
}
