<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { CSSProperties } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button } from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'

import {
  activeStep,
  activeTour,
  closeTour,
  isFirstStep,
  isLastStep,
  isRunning,
  isStepOffRoute,
  isTargetResolved,
  isTourCompleted,
  markTargetResolved,
  nextStep,
  previousStep,
  setTargetRect,
  setTourNavigating,
  skipTour,
  starterTour,
  startTour,
  stepBodyKey,
  stepCount,
  stepNumber,
  stepTitleKey,
  targetRect,
  tourTitleKey,
} from './store'
import type { TourRect, TourRole, TourStep } from './types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { t, te } = useI18n()

const EDGE = 16
const GAP = 12
const TARGET_PAD = 8
const TARGET_WAIT_MS = 1600
// Leaves at least 45% of the viewport for the tooltip when a target is
// taller than the screen.
const FOCUS_RATIO = 0.55

const reduce =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

const tooltipRef = ref<HTMLElement | null>(null)
const viewport = ref({ width: window.innerWidth, height: window.innerHeight })
const tooltipSize = ref({ width: 360, height: 200 })
// Height of the mobile tab bar, so the card never sits under it. Read from the
// DOM instead of a constant: the bar is hidden in focus mode and grows when the
// PWA adds the home-indicator padding.
const navInset = ref(0)

const role = computed<TourRole | null>(() => {
  if (auth.isAdmin) return 'staff'
  if (auth.isStudent) return 'student'
  if (auth.isStaff) return 'staff'
  return null
})

const title = computed(() => {
  const tour = activeTour.value
  const step = activeStep.value
  if (!tour || !step) return ''
  const key = stepTitleKey(tour.id, step.id)
  return te(key) ? t(key) : ''
})

const body = computed(() => {
  const tour = activeTour.value
  const step = activeStep.value
  if (!tour || !step) return ''
  const key = stepBodyKey(tour.id, step.id)
  return te(key) ? t(key) : ''
})

const spotlight = computed(() => isTargetResolved.value && !!targetRect.value)

const tourLabel = computed(() => {
  const tour = activeTour.value
  if (!tour) return ''
  const key = tourTitleKey(tour.id)
  return te(key) ? t(key) : ''
})

const hole = computed(() => {
  const rect = targetRect.value
  if (!rect) return null
  const width = viewport.value.width
  const height = viewport.value.height
  const top = Math.max(0, rect.top - TARGET_PAD)
  let bottom = Math.min(height, rect.top + rect.height + TARGET_PAD)
  // Sections taller than the viewport get a viewport-sized window so the
  // tooltip keeps its own space instead of the hole covering the whole screen.
  if (rect.height > height - EDGE * 2) {
    bottom = Math.min(bottom, top + Math.round(height * FOCUS_RATIO))
  }
  return {
    top,
    left: Math.max(0, rect.left - TARGET_PAD),
    right: Math.min(width, rect.left + rect.width + TARGET_PAD),
    bottom,
  }
})

const panels = computed(() => {
  const frame = hole.value
  if (!frame) return null
  return {
    top: { top: '0px', left: '0px', right: '0px', height: `${frame.top}px` },
    bottom: { top: `${frame.bottom}px`, left: '0px', right: '0px', bottom: '0px' },
    left: {
      top: `${frame.top}px`,
      left: '0px',
      width: `${frame.left}px`,
      height: `${frame.bottom - frame.top}px`,
    },
    right: {
      top: `${frame.top}px`,
      left: `${frame.right}px`,
      right: '0px',
      height: `${frame.bottom - frame.top}px`,
    },
  } as const
})

const ringStyle = computed<CSSProperties>(() => {
  const frame = hole.value
  if (!frame) return {}
  return {
    top: `${frame.top}px`,
    left: `${frame.left}px`,
    width: `${frame.right - frame.left}px`,
    height: `${frame.bottom - frame.top}px`,
    borderRadius: '10px',
    boxShadow:
      '0 0 0 2px var(--surface-blue-6), 0 0 0 7px color-mix(in srgb, var(--surface-blue-6) 22%, transparent)',
  }
})

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

const tooltipStyle = computed<CSSProperties>(() => {
  const width = viewport.value.width
  const height = viewport.value.height
  const frame = hole.value
  const measuredWidth = tooltipSize.value.width || 360
  const measuredHeight = tooltipSize.value.height || 200

  if (width < 640) {
    const topHalf = !frame || frame.top < height / 2
    const usable = height - EDGE * 2 - navInset.value
    return {
      left: `${EDGE}px`,
      width: `${width - EDGE * 2}px`,
      maxHeight: `${Math.max(180, usable)}px`,
      ...(topHalf
        ? {
            bottom: `calc(${EDGE + navInset.value}px + env(safe-area-inset-bottom, 0px))`,
          }
        : { top: `calc(${EDGE}px + env(safe-area-inset-top, 0px))` }),
    }
  }

  const boxWidth = Math.min(measuredWidth, width - EDGE * 2)

  if (!frame) {
    return {
      left: '50%',
      top: '50%',
      width: `${Math.min(420, width - EDGE * 2)}px`,
      transform: 'translate(-50%, -50%)',
    }
  }

  let placement = activeStep.value?.placement ?? 'bottom'
  if (placement === 'left' || placement === 'right') placement = 'bottom'

  const roomBelow = frame.bottom + GAP + measuredHeight <= height - EDGE
  const roomAbove = frame.top - GAP - measuredHeight >= EDGE

  if (placement === 'top' && !roomAbove) placement = 'bottom'
  else if (placement === 'bottom' && !roomBelow) placement = 'top'

  const style: CSSProperties = {
    width: `${boxWidth}px`,
    left: `${clamp((frame.left + frame.right) / 2 - boxWidth / 2, EDGE, width - boxWidth - EDGE)}px`,
  }

  if (!roomAbove && !roomBelow) {
    style.left = '50%'
    style.top = '50%'
    style.transform = 'translate(-50%, -50%)'
    return style
  }

  if (placement === 'top') {
    style.top = `${clamp(frame.top - GAP - measuredHeight, EDGE, height - measuredHeight - EDGE)}px`
  } else {
    style.top = `${clamp(frame.bottom + GAP, EDGE, height - measuredHeight - EDGE)}px`
  }
  return style
})

let restoreFocus: HTMLElement | null = null
const autoStartedFor = ref<string | null>(null)
let autoTimer: number | null = null
let resolveToken = 0
let targetEl: HTMLElement | null = null
let resizeObserver: ResizeObserver | null = null
let pollFrame = 0
let measureFrame = 0
let tooltipObserver: ResizeObserver | null = null

function isVisible(el: HTMLElement): boolean {
  const rect = el.getBoundingClientRect()
  return rect.width > 0 && rect.height > 0 && el.isConnected
}

function stopTargetTracking(): void {
  resolveToken += 1
  resizeObserver?.disconnect()
  resizeObserver = null
  targetEl = null
  cancelAnimationFrame(pollFrame)
  pollFrame = 0
  cancelAnimationFrame(measureFrame)
  measureFrame = 0
}

function updateViewport(): void {
  viewport.value = { width: window.innerWidth, height: window.innerHeight }
  const nav = document.querySelector<HTMLElement>('[data-slot="mobile-nav"]')
  navInset.value = nav ? Math.round(nav.getBoundingClientRect().height) : 0
}

function updateTargetRect(): void {
  if (!targetEl) return
  if (!targetEl.isConnected) {
    setTargetRect(null)
    return
  }
  const rect = targetEl.getBoundingClientRect()
  if (rect.width === 0 && rect.height === 0) {
    setTargetRect(null)
    return
  }
  const next: TourRect = {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  }
  setTargetRect(next)
}

function measureDuringScroll(duration: number): void {
  const until = performance.now() + duration
  const loop = () => {
    updateTargetRect()
    if (performance.now() < until) measureFrame = requestAnimationFrame(loop)
  }
  loop()
}

function resolveTarget(step: TourStep): void {
  stopTargetTracking()
  const token = resolveToken

  if (!step.target) {
    markTargetResolved()
    return
  }

  const startedAt = performance.now()
  const finish = (el: HTMLElement) => {
    targetEl = el
    resizeObserver = new ResizeObserver(updateTargetRect)
    resizeObserver.observe(el)
    updateTargetRect()
    markTargetResolved()
  }

  const attempt = () => {
    if (token !== resolveToken) return
    const el = document.querySelector<HTMLElement>(
      `[data-tour="${CSS.escape(step.target!)}"]`,
    )
    if (el && isVisible(el)) {
      const rect = el.getBoundingClientRect()
      const oversized = rect.height > window.innerHeight - EDGE * 2
      if (oversized || rect.top < EDGE || rect.bottom > window.innerHeight - EDGE) {
        el.scrollIntoView({
          block: oversized ? 'start' : 'center',
          inline: 'nearest',
          behavior: reduce ? 'auto' : 'smooth',
        })
        measureDuringScroll(650)
      }
      finish(el)
      return
    }
    if (performance.now() - startedAt < TARGET_WAIT_MS) {
      pollFrame = requestAnimationFrame(attempt)
    } else {
      markTargetResolved()
    }
  }

  attempt()
}

async function ensureRoute(step: TourStep): Promise<void> {
  if (!step.route) return
  if (router.currentRoute.value.name === step.route.name) return
  setTourNavigating(true)
  try {
    await router.push(step.route)
  } catch {
    // A guard can abort navigation; the step falls back to a centered card.
  } finally {
    setTourNavigating(false)
  }
  await nextTick()
}

async function enterStep(step: TourStep): Promise<void> {
  await ensureRoute(step)
  if (!activeStep.value || activeStep.value.id !== step.id) return
  await nextTick()
  resolveTarget(step)
}

watch(
  () => {
    const tour = activeTour.value
    const step = activeStep.value
    return tour && step ? `${tour.id}:${step.id}` : ''
  },
  () => {
    const step = activeStep.value
    if (!step) {
      stopTargetTracking()
      return
    }
    void enterStep(step)
  },
  { immediate: true },
)

// A step can stay active while the user navigates (the tour now survives a
// detour), so re-resolve the target for the new page instead of leaving the
// spotlight empty until the next step.
watch(
  () => route.name,
  async () => {
    const step = activeStep.value
    if (!step) return
    await nextTick()
    resolveTarget(step)
  },
)

watch(
  [isRunning, isTargetResolved],
  async ([running, resolved]) => {
    if (running && resolved) {
      await nextTick()
      tooltipRef.value?.focus()
    }
  },
  { flush: 'post' },
)

watch(isRunning, (running) => {
  if (running) {
    restoreFocus = document.activeElement as HTMLElement | null
  } else if (restoreFocus?.isConnected) {
    restoreFocus.focus()
    restoreFocus = null
  }
})

watch(
  tooltipRef,
  (el) => {
    tooltipObserver?.disconnect()
    tooltipObserver = null
    if (!el) return
    tooltipObserver = new ResizeObserver(() => {
      tooltipSize.value = { width: el.offsetWidth, height: el.offsetHeight }
      updateViewport()
    })
    tooltipObserver.observe(el)
    tooltipSize.value = { width: el.offsetWidth, height: el.offsetHeight }
  },
  { flush: 'post' },
)

function isTypingTarget(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null
  if (!el) return false
  return (
    el.tagName === 'INPUT' ||
    el.tagName === 'TEXTAREA' ||
    el.tagName === 'SELECT' ||
    el.isContentEditable
  )
}

function onNext(): void {
  nextStep(auth.user?.id)
}

function onSkip(): void {
  skipTour(auth.user?.id)
}

function onWindowKeydown(event: KeyboardEvent): void {
  if (!isRunning.value) return
  if (event.key === 'Escape') {
    event.preventDefault()
    closeTour()
    return
  }
  if (isTypingTarget(event.target)) return
  if (event.key === 'ArrowRight') {
    event.preventDefault()
    onNext()
  } else if (event.key === 'ArrowLeft') {
    event.preventDefault()
    previousStep()
  }
}

function onTooltipKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Tab') return
  const root = tooltipRef.value
  if (!root) return
  const focusables = Array.from(
    root.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
    ),
  )
  if (!focusables.length) {
    event.preventDefault()
    return
  }
  const first = focusables[0]!
  const last = focusables[focusables.length - 1]!
  const active = document.activeElement
  if (event.shiftKey) {
    if (active === first || active === root) {
      event.preventDefault()
      last.focus()
    }
  } else if (active === last) {
    event.preventDefault()
    first.focus()
  } else if (!root.contains(active)) {
    event.preventDefault()
    first.focus()
  }
}

function onViewportChange(): void {
  updateViewport()
  updateTargetRect()
}

function maybeAutoStart(): void {
  if (!auth.checked || !auth.user || !route.meta.requiresAuth) return
  if (isRunning.value || autoTimer !== null) return
  const userId = auth.user.id
  if (autoStartedFor.value === userId) return
  const tourRole = role.value
  if (!tourRole) return
  const starter = starterTour(tourRole)
  autoStartedFor.value = userId
  if (!starter || isTourCompleted(userId, starter.id)) return
  autoTimer = window.setTimeout(() => {
    autoTimer = null
    if (!isRunning.value) startTour(starter.id)
  }, 600)
}

watch(
  () => [auth.checked, auth.user?.id, route.meta.requiresAuth, route.name] as const,
  () => maybeAutoStart(),
  { immediate: true },
)

watch(
  () => auth.user?.id ?? null,
  (userId, previous) => {
    if (userId === previous) return
    if (isRunning.value) closeTour()
    if (!userId) {
      autoStartedFor.value = null
      if (autoTimer !== null) {
        window.clearTimeout(autoTimer)
        autoTimer = null
      }
      return
    }
    maybeAutoStart()
  },
)

onMounted(() => {
  window.addEventListener('keydown', onWindowKeydown)
  window.addEventListener('scroll', onViewportChange, true)
  window.addEventListener('resize', onViewportChange)
  updateViewport()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onWindowKeydown)
  window.removeEventListener('scroll', onViewportChange, true)
  window.removeEventListener('resize', onViewportChange)
  if (autoTimer !== null) window.clearTimeout(autoTimer)
  stopTargetTracking()
  tooltipObserver?.disconnect()
})
</script>

<template>
  <Teleport to="body">
    <div v-if="activeTour" class="text-start" aria-live="polite">
      <template v-if="spotlight && panels">
        <div class="fixed z-[200] bg-black/60" :style="panels.top" />
        <div class="fixed z-[200] bg-black/60" :style="panels.bottom" />
        <div class="fixed z-[200] bg-black/60" :style="panels.left" />
        <div class="fixed z-[200] bg-black/60" :style="panels.right" />
        <div
          class="pointer-events-none fixed z-[200]"
          :style="ringStyle"
          aria-hidden="true"
        />
      </template>
      <!-- Off-route: the user took a detour, so leave the page usable and keep
           the card floating instead of blocking the whole screen. -->
      <div v-else-if="!isStepOffRoute" class="fixed inset-0 z-[200] bg-black/60" />

      <div
        ref="tooltipRef"
        role="dialog"
        :aria-modal="!isStepOffRoute"
        :aria-label="title"
        aria-describedby="tour-step-body"
        tabindex="-1"
        class="fixed z-[201] max-h-[calc(100dvh-2rem)] overflow-y-auto rounded-6 border border-outline-gray-2 bg-surface-elevation-1 p-4 text-start shadow-2xl outline-none transition-all duration-150"
        :style="tooltipStyle"
        @keydown="onTooltipKeydown"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-p-xs text-ink-gray-5">
              {{
                t('tour.controls.step', {
                  current: stepNumber,
                  total: stepCount,
                })
              }}
              <template v-if="tourLabel"> · {{ tourLabel }}</template>
            </p>
            <h2 class="mt-1 text-lg-semibold text-ink-gray-9">{{ title }}</h2>
          </div>
          <button
            type="button"
            class="-mr-1 -mt-1 flex size-7 shrink-0 items-center justify-center rounded-4 text-ink-gray-5 hover:bg-surface-gray-2"
            :aria-label="t('tour.controls.close')"
            @click="closeTour"
          >
            <span class="lucide-x size-4" aria-hidden="true" />
          </button>
        </div>

        <p id="tour-step-body" class="mt-2 text-p-sm text-ink-gray-6">{{ body }}</p>

        <p
          v-if="isStepOffRoute"
          class="mt-2 rounded-4 bg-surface-gray-2 px-2 py-1.5 text-p-xs text-ink-gray-6"
        >
          {{ t('tour.controls.offRoute') }}
        </p>

        <div class="mt-4 flex items-center justify-between gap-2">
          <Button
            variant="ghost"
            theme="gray"
            :label="t('tour.controls.skip')"
            @click="onSkip"
          />
          <div class="flex items-center gap-2">
            <Button
              v-if="!isFirstStep"
              variant="outline"
              theme="gray"
              :label="t('tour.controls.back')"
              @click="previousStep"
            />
            <Button
              variant="solid"
              :label="isLastStep ? t('tour.controls.finish') : t('tour.controls.next')"
              @click="onNext"
            />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
