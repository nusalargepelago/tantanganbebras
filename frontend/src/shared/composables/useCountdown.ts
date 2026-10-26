import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

/**
 * Ticking countdown to an absolute deadline (epoch ms).
 * `deadline` is a getter so it can be set after data loads.
 * Returns remaining ms (null when there is no deadline) + a MM:SS/HH:MM:SS formatter.
 */
export function useCountdown(deadline: () => number | null, onExpire?: () => void) {
  const now = ref(Date.now())
  const expired = ref(false)
  let fired = false
  let timer: ReturnType<typeof setInterval> | null = null

  const timeLeft = computed(() => {
    const d = deadline()
    if (d == null) return null
    return Math.max(0, d - now.value)
  })

  const running = computed(() => timeLeft.value !== null && timeLeft.value > 0)

  function format(ms: number): string {
    const total = Math.floor(ms / 1000)
    const h = Math.floor(total / 3600)
    const m = Math.floor((total % 3600) / 60)
    const s = total % 60
    const pad = (n: number) => String(n).padStart(2, '0')
    return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`
  }

  function tick() {
    now.value = Date.now()
    if (timeLeft.value !== null && timeLeft.value <= 0 && !fired) {
      fired = true
      expired.value = true
      onExpire?.()
    }
  }

  onMounted(() => {
    tick()
    timer = setInterval(tick, 1000)
  })

  onBeforeUnmount(() => {
    if (timer) clearInterval(timer)
  })

  return { timeLeft, expired, running, format }
}
