<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Skeleton } from 'frappe-ui'

import { useQuestionStore } from '../store'
import { categoryLabel } from '@/shared/labels'
import TopicRow from './TopicRow.vue'

const CATEGORIES = ['cub', 'scout', 'rover'] as const

const props = defineProps<{ activeQuestion?: string }>()
const emit = defineEmits<{
  select: [name: string]
  addTopic: [category: string]
  editTopic: [name: string]
  deleteTopic: [name: string]
  deleteQuestion: [name: string]
}>()

const store = useQuestionStore()
const { t } = useI18n()
const expanded = ref<Record<string, boolean>>({})

const loading = computed(() => store.loading || store.topicsLoading)

function topicsFor(category: string) {
  return store.topics
    .filter((t) => t.category === category)
    .sort((a, b) => a.idx - b.idx)
}

function questionsFor(topicName: string) {
  return store.items.filter((q) => q.topicId === topicName)
}

function unassignedFor(category: string) {
  return store.items.filter((q) => q.category === category && !q.topicId)
}

function isExpanded(key: string) {
  return expanded.value[key] ?? true
}

function toggle(key: string) {
  expanded.value[key] = !isExpanded(key)
}

watch(
  () => props.activeQuestion,
  (name) => {
    if (!name) return
    const q = store.items.find((item) => item.name === name)
    if (q?.topicId) expanded.value[q.topicId] = true
  },
  { immediate: true },
)

onMounted(async () => {
  await Promise.all([store.listTopics(), store.list({ perPage: 200 })])
})
</script>

<template>
  <div class="flex h-full flex-col">
    <div class="border-b border-outline-gray-1 px-4 py-3">
      <p class="text-base-medium text-ink-gray-8">{{ t('editor.outline') }}</p>
    </div>

    <div class="flex-1 space-y-4 overflow-y-auto p-3">
      <template v-if="loading">
        <Skeleton v-for="i in 4" :key="i" class="h-8" />
      </template>

      <template v-else>
        <div
          v-if="store.topics.length === 0 && store.items.length === 0"
          class="flex flex-col items-center gap-2 py-8 text-center"
        >
          <span class="lucide-folder-open size-8 text-ink-gray-4" aria-hidden="true" />
          <p class="text-p-sm text-ink-gray-5">{{ t('editor.noTopics') }}</p>
          <Button
            variant="outline"
            theme="gray"
            icon-left="lucide-plus"
            :label="t('question.addTopic', { category: categoryLabel('cub') })"
            @click="emit('addTopic', 'cub')"
          />
        </div>

        <template v-else>
          <div v-for="category in CATEGORIES" :key="category" class="space-y-1">
          <div class="flex flex-wrap items-center justify-between gap-x-2 gap-y-1 px-1">
            <span class="text-p-xs-semibold uppercase tracking-wide text-ink-gray-5">
              {{ categoryLabel(category) }}
            </span>
            <Button
              variant="ghost"
              theme="gray"
              size="sm"
              icon-left="lucide-plus"
              class="min-w-0"
              :label="t('question.addTopic', { category: categoryLabel(category) })"
              @click="emit('addTopic', category)"
            />
          </div>

          <TopicRow
            v-for="topic in topicsFor(category)"
            :key="topic.name"
            :topic="topic"
            :questions="questionsFor(topic.name)"
            :active-question="activeQuestion"
            :expanded="isExpanded(topic.name)"
            @toggle="toggle(topic.name)"
            @select="emit('select', $event)"
            @edit="emit('editTopic', topic.name)"
            @delete="emit('deleteTopic', topic.name)"
            @delete-question="emit('deleteQuestion', $event)"
          />

          <div v-if="unassignedFor(category).length" class="space-y-0.5">
            <p class="px-2 text-p-xs text-ink-gray-4">{{ t('editor.noTopic') }}</p>
            <div
              v-for="q in unassignedFor(category)"
              :key="q.name"
              class="group/q flex cursor-pointer items-center gap-2 rounded-4 px-2 py-1 hover:bg-surface-gray-2"
              :class="q.name === activeQuestion ? 'bg-surface-blue-2' : ''"
              @click="emit('select', q.name)"
            >
              <span class="lucide-file-question size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
              <span class="min-w-0 flex-1 truncate text-p-sm text-ink-gray-8">
                {{ q.questionCode }}
              </span>
              <Button
                variant="ghost"
                theme="red"
                icon="lucide-trash-2"
                :label="t('editor.deleteQuestion')"
                size="sm"
                class="shrink-0 opacity-0 transition-opacity group-hover/q:opacity-100"
                @click.stop="emit('deleteQuestion', q.name)"
              />
            </div>
          </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
