<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton, dialog, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { categoryLabel } from '@/shared/labels'
import { useEventStudentStore } from '@/features/event-student/store'
import { useEventStore } from '../store'

const route = useRoute()
const router = useRouter()
const store = useEventStore()
const eventStudent = useEventStudentStore()
const { t } = useI18n()

const name = computed(() => route.params.name as string)
const event = computed(() => store.current)
const testing = ref(false)

function text(q: Record<string, any>): string {
  return (q.question ?? '').replace(/<[^>]*>/g, '').trim() || q.questionCode || '(untitled)'
}

function onDelete() {
  dialog.danger({
    title: t('event.deleteTitle'),
    message: t('event.deleteMessage', { name: event.value?.eventName ?? '' }),
    onConfirm: async () => {
      const ok = await store.softDelete(name.value)
      if (!ok) throw new Error(store.error || 'Failed to delete event')
      toast.success(t('event.deletedToast'))
      router.push({ name: 'EventList' })
    },
  })
}

async function onRestore() {
  const restored = await store.restore(name.value)
  if (!restored) {
    toast.error(store.error || t('event.restoreFailed'))
    return
  }
  toast.success(t('event.restoreToast'))
  await store.get(name.value)
}

async function onTest() {
  if (testing.value) return
  testing.value = true
  const attempt = await eventStudent.make(name.value, true)
  testing.value = false
  if (!attempt) {
    toast.error(eventStudent.error || t('event.testFailed'))
    return
  }
  router.push({ name: 'EventStudentRunner', params: { name: attempt.name } })
}

onMounted(() => store.get(name.value))
</script>

<template>
  <AppPageHeader :title="event?.eventName || t('route.EventDetail.title')">
    <template #actions>
      <Button
        v-if="event && event.disabled"
        variant="outline"
        theme="green"
        icon-left="lucide-rotate-ccw"
        :label="t('list.restore')"
        @click="onRestore"
      />
      <Button
        v-else-if="event"
        variant="outline"
        theme="red"
        icon-left="lucide-trash-2"
        :label="t('list.delete')"
        @click="onDelete"
      />
      <Button
        variant="outline"
        theme="gray"
        :label="t('list.edit')"
        :route="{ name: 'EventEdit', params: { name } }"
      />
      <Button
        variant="outline"
        theme="gray"
        icon-left="lucide-play"
        :label="t('event.testQuiz')"
        :loading="testing"
        @click="onTest"
      />
      <Button
        variant="solid"
        :label="t('event.viewResults')"
        :route="{ name: 'EventResults', params: { name } }"
        data-tour="admin-event-results"
      />
    </template>
    <template #mobile-actions>
      <Button
        v-if="event && event.disabled"
        variant="ghost"
        icon="lucide-rotate-ccw"
        :label="t('list.restore')"
        @click="onRestore"
      />
      <Button
        v-else-if="event"
        variant="ghost"
        icon="lucide-trash-2"
        :label="t('list.delete')"
        @click="onDelete"
      />
      <Button
        variant="ghost"
        icon="lucide-pencil"
        :label="t('list.edit')"
        :route="{ name: 'EventEdit', params: { name } }"
      />
      <Button
        variant="ghost"
        icon="lucide-list"
        :label="t('event.viewResults')"
        :route="{ name: 'EventResults', params: { name } }"
        data-tour="admin-event-results"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <Skeleton v-if="store.currentLoading" class="h-40" />
    <ErrorMessage v-else-if="store.error" :message="store.error" />

    <template v-else-if="event">
      <div class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <div class="flex flex-wrap items-center gap-2">
          <h1 class="text-2xl-semibold text-ink-gray-8">{{ event.eventName }}</h1>
          <Badge
            v-if="event.disabled"
            :label="t('list.deleted')"
            theme="red"
            variant="subtle"
          />
          <Badge
            v-else
            :label="event.published ? 'Published' : 'Draft'"
            :theme="event.published ? 'green' : 'gray'"
            variant="subtle"
          />
        </div>
        <p class="text-p-sm text-ink-gray-5">
          {{
            t('event.metaLine', {
              category: categoryLabel(event.category),
              minutes: event.timeLimit,
              deadline: new Date(event.eventDeadline).toLocaleString(),
            })
          }}
        </p>
        <p v-if="event.description" class="whitespace-pre-wrap text-p-sm text-ink-gray-8">
          {{ event.description }}
        </p>
      </div>

      <section class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <h2 class="text-xl-semibold text-ink-gray-8">
          {{ t('event.questionsCount', { count: event.questions.length }) }}
        </h2>
        <ol class="mt-3 space-y-2">
          <li
            v-for="(q, i) in event.questions"
            :key="q.name"
            class="flex gap-2 border-b border-outline-gray-1 pb-2 text-p-sm last:border-0 last:pb-0"
          >
            <span class="text-ink-gray-5">{{ i + 1 }}.</span>
            <span class="min-w-0 whitespace-pre-wrap text-ink-gray-8">{{ text(q) }}</span>
          </li>
        </ol>
      </section>
    </template>
  </div>
</template>
