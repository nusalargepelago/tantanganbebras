<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, Dropdown } from 'frappe-ui'

import type { Question, Topic } from '../store'
import { stripTags } from '@/shared/richText'

const props = defineProps<{
  topic: Topic
  questions: Question[]
  activeQuestion?: string
  expanded: boolean
}>()

const emit = defineEmits<{
  toggle: []
  select: [name: string]
  edit: []
  delete: []
  deleteQuestion: [name: string]
}>()

const { t } = useI18n()

const countLabel = computed(() => t('editor.topicCount', { n: props.questions.length }))

function questionLabel(q: Question) {
  const text = stripTags(q.question)
  if (!text) return t('editor.untitled')
  return text.length > 80 ? `${text.slice(0, 80)}.` : text
}

function rowActions() {
  return [
    { label: t('editor.editTopic'), icon: 'lucide-pencil', onClick: () => emit('edit') },
    { label: t('editor.deleteTopic'), icon: 'lucide-trash-2', onClick: () => emit('delete') },
  ]
}
</script>

<template>
  <div class="rounded-4">
    <div
      class="group flex cursor-pointer items-center gap-2 rounded-4 px-2 py-1.5 hover:bg-surface-gray-2"
      @click="emit('toggle')"
    >
      <span
        class="text-ink-gray-4 transition-transform"
        :class="expanded ? 'rotate-90' : ''"
        aria-hidden="true"
      >
        <span class="lucide-chevron-right size-4" />
      </span>
      <span class="min-w-0 flex-1 truncate text-base-medium text-ink-gray-8">
        {{ topic.title }}
      </span>
      <span class="shrink-0 text-p-xs text-ink-gray-5">{{ countLabel }}</span>
      <Dropdown v-if="true" :options="rowActions()" align="end" @click.stop>
        <Button
          variant="ghost"
          theme="gray"
          icon="lucide-more-horizontal"
          :label="t('editor.topicActions')"
          class="opacity-0 transition-opacity group-hover:opacity-100"
          @click.stop
        />
      </Dropdown>
    </div>

    <div v-if="expanded" class="ml-4 space-y-0.5 border-l border-outline-gray-1 pl-2">
      <p v-if="questions.length === 0" class="px-2 py-1 text-p-xs text-ink-gray-4">
        {{ t('editor.noQuestionsInTopic') }}
      </p>
      <div
        v-for="q in questions"
        :key="q.name"
        class="group/q flex cursor-pointer items-center gap-2 rounded-4 px-2 py-1 hover:bg-surface-gray-2"
        :class="q.name === activeQuestion ? 'bg-surface-blue-2' : ''"
        @click="emit('select', q.name)"
      >
        <span class="lucide-help-circle size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
        <span class="min-w-0 flex-1 truncate text-p-sm text-ink-gray-8">
          {{ questionLabel(q) }}
        </span>
        <Badge
          :label="q.questionType === 'Essay' ? t('list.essay') : 'MC'"
          :theme="q.questionType === 'Essay' ? 'blue' : 'gray'"
          variant="subtle"
          class="shrink-0"
        />
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
