<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Dialog, type DialogAction } from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'

import {
  catalogOpen,
  closeCatalog,
  isTourCompleted,
  startTour,
  tourDescriptionKey,
  tourTitleKey,
  toursForRole,
} from './store'
import type { TourRole } from './types'

const auth = useAuthStore()
const { t } = useI18n()

const role = computed<TourRole | null>(() => {
  if (auth.isAdmin) return 'staff'
  if (auth.isStudent) return 'student'
  if (auth.isStaff) return 'staff'
  return null
})

const tours = computed(() => toursForRole(role.value))
const completed = ref<Record<string, boolean>>({})

watch(
  catalogOpen,
  (open) => {
    if (!open) return
    const userId = auth.user?.id
    const next: Record<string, boolean> = {}
    for (const tour of tours.value) {
      next[tour.id] = userId ? isTourCompleted(userId, tour.id) : false
    }
    completed.value = next
  },
  { immediate: true },
)

const actions = computed<DialogAction[]>(() => [
  { label: t('tour.catalog.close'), variant: 'outline', onClick: closeCatalog },
])
</script>

<template>
  <Dialog
    :open="catalogOpen"
    :title="t('tour.catalog.title')"
    icon="lucide-compass"
    theme="blue"
    :actions="actions"
    @update:open="(open: boolean) => (!open ? closeCatalog() : undefined)"
  >
    <div class="space-y-3" data-tour="tour-catalog">
      <p class="text-p-sm text-ink-gray-5">{{ t('tour.catalog.subtitle') }}</p>
      <div
        v-for="tour in tours"
        :key="tour.id"
        class="flex flex-wrap items-start gap-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-4"
      >
        <span
          :class="`${tour.icon ?? 'lucide-compass'} mt-0.5 size-5 shrink-0 text-ink-gray-5`"
          aria-hidden="true"
        />
        <div class="min-w-0 flex-1 basis-48">
          <div class="flex flex-wrap items-center gap-2">
            <p class="text-base-medium text-ink-gray-9">
              {{ t(tourTitleKey(tour.id)) }}
            </p>
            <span
              v-if="completed[tour.id]"
              class="rounded-3 bg-surface-green-2 px-1.5 py-0.5 text-p-xs text-ink-green-7"
            >
              {{ t('tour.catalog.completed') }}
            </span>
          </div>
          <p class="mt-1 text-p-sm text-ink-gray-5">
            {{ t(tourDescriptionKey(tour.id)) }}
          </p>
          <p class="mt-1 text-p-xs text-ink-gray-4">
            {{ t('tour.catalog.steps', { count: tour.steps.length }) }}
          </p>
        </div>
        <Button
          class="ml-auto shrink-0"
          variant="solid"
          theme="gray"
          :label="
            completed[tour.id] ? t('tour.catalog.replay') : t('tour.catalog.start')
          "
          @click="startTour(tour.id)"
        />
      </div>

      <p v-if="!tours.length" class="text-p-sm text-ink-gray-5">
        {{ t('tour.catalog.empty') }}
      </p>
    </div>
  </Dialog>
</template>
