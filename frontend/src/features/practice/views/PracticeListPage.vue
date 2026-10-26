<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { categoryLabel } from '@/shared/labels'

import { usePracticeStore, type Practice } from '../store'

const router = useRouter()
const store = usePracticeStore()
const { t } = useI18n()

const empty = computed(() => !store.loading && store.mine.length === 0)

function statusOf(p: Practice) {
  if (p.finishedAt) return { label: t('list.completed'), theme: 'green' as const }
  if (p.startedAt) return { label: t('list.notSubmitted'), theme: 'amber' as const }
  return null
}

function scoreLabel(p: Practice): string {
  return p.finishedAt && p.score != null
    ? t('practice.scoreWith', { score: p.score })
    : t('practice.notGraded')
}

function durationLabel(p: Practice): string {
  if (p.startedAt && p.finishedAt) {
    const mins = Math.max(
      0,
      Math.round(
        (Date.parse(p.finishedAt) - Date.parse(p.startedAt)) / 60000,
      ),
    )
    if (mins >= 60) return t('practice.durationHours', { n: Math.round(mins / 60) })
    return t('practice.durationMinutes', { n: mins })
  }
  if (p.timeLimit) return t('practice.limitMinutes', { n: p.timeLimit })
  return '—'
}

async function onStart() {
  const created = await store.create()
  if (!created) {
    toast.error(store.error || t('practice.startFailed'))
    return
  }
  toast.success(t('practice.createdToast'))
  await router.push({ name: 'PracticeRunner' })
}

function open(p: Practice) {
  router.push({ name: 'PracticeResult', params: { name: p.name } })
}

onMounted(store.listMine)
</script>

<template>
  <AppPageHeader>
    <template #actions>
      <Button
        variant="solid"
        icon-left="lucide-play"
        :label="t('practice.startPractice')"
        :disabled="store.loading"
        data-tour="student-practice-start"
        @click="onStart"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-play"
        :label="t('practice.startPractice')"
        :disabled="store.loading"
        data-tour="student-practice-start"
        @click="onStart"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6" data-tour="student-practice-list">
    <ErrorMessage v-if="store.error" :message="store.error" />

    <div v-if="store.loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Skeleton v-for="i in 6" :key="i" class="h-36" />
    </div>

    <div
      v-else-if="empty"
      class="flex flex-col items-center gap-2 rounded-6 border border-outline-gray-1 py-12 text-center"
    >
      <span class="lucide-clipboard-list size-8 text-ink-gray-4" aria-hidden="true" />
      <p class="text-p-sm text-ink-gray-5">{{ t('practice.noData') }}</p>
      <Button
        variant="outline"
        theme="gray"
        icon-left="lucide-play"
        :label="t('practice.startPractice')"
        @click="onStart"
      />
    </div>

    <div
      v-else
      class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      data-tour="student-practice-history"
    >
      <div
        v-for="p in store.mine"
        :key="p.name"
        class="flex cursor-pointer flex-col gap-2 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-4 text-left transition-colors hover:border-outline-gray-3"
        @click="open(p)"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="text-base-medium text-ink-gray-8">
            {{
              t('practice.cardTitle', {
                date: p.createdAt ? new Date(p.createdAt).toLocaleDateString() : p.name,
              })
            }}
          </span>
          <Badge
            v-if="statusOf(p)"
            :label="statusOf(p)!.label"
            :theme="statusOf(p)!.theme"
            variant="subtle"
          />
        </div>
        <div class="flex items-center gap-2">
          <Badge :label="categoryLabel(p.category)" variant="subtle" />
        </div>
        <div class="mt-auto flex items-center justify-between text-p-sm">
          <span class="text-ink-gray-8">{{ scoreLabel(p) }}</span>
          <span class="text-ink-gray-5">{{ durationLabel(p) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
