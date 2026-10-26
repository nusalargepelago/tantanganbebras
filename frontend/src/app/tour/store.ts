import { computed, reactive } from 'vue'

import { TOUR_BY_ID, TOURS } from './tours'
import type { TourDefinition, TourRect, TourRole, TourStep } from './types'

const STORAGE_PREFIX = 'minimals-tour:v1'

interface TourState {
  tourId: string | null
  stepIndex: number
  rect: TourRect | null
  targetResolved: boolean
  catalogOpen: boolean
  navigating: boolean
  routeName: string | null
}

const state = reactive<TourState>({
  tourId: null,
  stepIndex: 0,
  rect: null,
  targetResolved: false,
  catalogOpen: false,
  navigating: false,
  routeName: null,
})

export const activeTour = computed<TourDefinition | null>(() =>
  state.tourId ? (TOUR_BY_ID.get(state.tourId) ?? null) : null,
)
export const activeStep = computed<TourStep | null>(
  () => activeTour.value?.steps[state.stepIndex] ?? null,
)
export const stepCount = computed(() => activeTour.value?.steps.length ?? 0)
export const stepNumber = computed(() => state.stepIndex + 1)
export const isFirstStep = computed(() => state.stepIndex === 0)
export const isLastStep = computed(
  () => !!activeTour.value && state.stepIndex >= activeTour.value.steps.length - 1,
)
export const isRunning = computed(() => !!activeTour.value)
export const targetRect = computed(() => state.rect)
export const isTargetResolved = computed(() => state.targetResolved)
export const catalogOpen = computed(() => state.catalogOpen)
/** True when the running step belongs to a page the user has navigated away from. */
export const isStepOffRoute = computed(() => {
  const step = activeStep.value
  const name = state.routeName
  if (!step || !name) return false
  const names = step.match ?? step.route?.name
  if (!names) return false
  return Array.isArray(names) ? !names.includes(name) : names !== name
})

export function stepTitleKey(tourId: string, stepId: string): string {
  return `tour.${tourId}.steps.${stepId}.title`
}

export function stepBodyKey(tourId: string, stepId: string): string {
  return `tour.${tourId}.steps.${stepId}.body`
}

export function tourTitleKey(tourId: string): string {
  return `tour.${tourId}.title`
}

export function tourDescriptionKey(tourId: string): string {
  return `tour.${tourId}.description`
}

export function toursForRole(role: TourRole | null): TourDefinition[] {
  if (!role) return []
  return TOURS.filter((tour) => tour.roles.includes(role))
}

export function starterTour(role: TourRole): TourDefinition | undefined {
  return TOURS.find((tour) => tour.starter && tour.roles.includes(role))
}

function storageKey(userId: string, tourId: string): string {
  return `${STORAGE_PREFIX}:${userId}:${tourId}`
}

export function isTourCompleted(userId: string, tourId: string): boolean {
  try {
    return localStorage.getItem(storageKey(userId, tourId)) === 'done'
  } catch {
    return false
  }
}

export function markTourCompleted(userId: string, tourId: string): void {
  try {
    localStorage.setItem(storageKey(userId, tourId), 'done')
  } catch {
    // Storage can be unavailable (private mode); the tour still runs.
  }
}

function matchesStep(step: TourStep, routeName: string): boolean {
  const names = step.match ?? (step.route ? step.route.name : undefined)
  if (!names) return false
  return Array.isArray(names) ? names.includes(routeName) : names === routeName
}

function resetTarget(): void {
  state.rect = null
  state.targetResolved = false
}

export function setTargetRect(rect: TourRect | null): void {
  state.rect = rect
}

export function markTargetResolved(): void {
  state.targetResolved = true
}

export function setTourNavigating(navigating: boolean): void {
  state.navigating = navigating
}

export function openCatalog(): void {
  state.catalogOpen = true
}

export function closeCatalog(): void {
  state.catalogOpen = false
}

export function startTour(tourId: string): void {
  if (!TOUR_BY_ID.has(tourId)) return
  state.catalogOpen = false
  state.tourId = tourId
  state.stepIndex = 0
  resetTarget()
}

export function nextStep(userId: string | null | undefined): void {
  const tour = activeTour.value
  if (!tour) return
  if (state.stepIndex >= tour.steps.length - 1) {
    completeActive(userId)
    return
  }
  state.stepIndex += 1
  resetTarget()
}

export function previousStep(): void {
  if (state.stepIndex === 0) return
  state.stepIndex -= 1
  resetTarget()
}

function completeActive(userId: string | null | undefined): void {
  if (userId && activeTour.value) markTourCompleted(userId, activeTour.value.id)
  stopTour()
}

export function skipTour(userId: string | null | undefined): void {
  completeActive(userId)
}

/** Leaves the tour without marking it complete, so it can auto-start again. */
export function closeTour(): void {
  stopTour()
}

function stopTour(): void {
  state.tourId = null
  state.stepIndex = 0
  state.navigating = false
  resetTarget()
}

/**
 * Called from `router.afterEach`. Keeps the tour in sync when the user clicks
 * through a highlighted target instead of pressing Next.
 */
export function onTourRouteChange(routeName: string | null | undefined): void {
  state.routeName = routeName ?? null
  const tour = activeTour.value
  const current = activeStep.value
  if (!tour || !current || state.navigating || !routeName) return

  if (current.advanceOnRoute) {
    const next = tour.steps[state.stepIndex + 1]
    if (next && matchesStep(next, routeName)) {
      state.stepIndex += 1
      resetTarget()
      return
    }
  }

  for (let index = state.stepIndex + 1; index < tour.steps.length; index += 1) {
    if (matchesStep(tour.steps[index]!, routeName)) {
      state.stepIndex = index
      resetTarget()
      return
    }
  }

  if (matchesStep(current, routeName)) {
    resetTarget()
    return
  }

  // The user navigated outside the tour's routes. Keep the tour alive on the
  // same step — dropping it here made any detour (a nav tab, a back button)
  // silently end the tour. The card re-centres and explains how to resume.
  resetTarget()
}
