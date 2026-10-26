<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge } from 'frappe-ui'

import { OPTION_LETTERS, optionKey } from '@/shared/questionOptions'
import { hasRichContent } from '@/shared/richText'
import { sanitizeHtml } from '@/shared/sanitize'

type QuestionOptionSource = {
  questionType?: string | null
  correctAnswer?: string | null
} & Record<string, any>

const props = defineProps<{
  question: QuestionOptionSource | null
  selected?: string | null
  showCorrect?: boolean
  selectedCorrect?: boolean | null
}>()

const { t } = useI18n()

const options = computed(() => {
  const question = props.question
  if (!question || question.questionType !== 'Multiple Choice') return []
  const selected = (props.selected ?? '').toLowerCase()
  const correct = (question.correctAnswer ?? '').toLowerCase()
  return OPTION_LETTERS.map((letter) => ({
    letter,
    text: (question[optionKey(letter)] as string | null | undefined) ?? '',
    isSelected: selected === letter,
    isCorrect: props.showCorrect === true && correct === letter,
  }))
})

type OptionRow = { isSelected: boolean; isCorrect: boolean }

function selectedIsCorrect(option: OptionRow): boolean {
  if (props.selectedCorrect !== undefined && props.selectedCorrect !== null) {
    return props.selectedCorrect
  }
  return option.isCorrect
}

function rowClass(option: OptionRow): string {
  if (option.isSelected) {
    return selectedIsCorrect(option)
      ? 'border-outline-green-7 bg-surface-green-2'
      : 'border-outline-red-7 bg-surface-red-2'
  }
  return option.isCorrect
    ? 'border-outline-green-7 bg-surface-green-2'
    : 'border-outline-gray-1'
}

function letterClass(option: OptionRow): string {
  if (option.isSelected) {
    return selectedIsCorrect(option)
      ? 'bg-surface-green-7 text-white'
      : 'bg-surface-red-7 text-white'
  }
  return option.isCorrect
    ? 'bg-surface-green-7 text-white'
    : 'bg-surface-gray-2 text-ink-gray-6'
}
</script>

<template>
  <div v-if="options.length" class="mt-2 space-y-1.5">
    <div
      v-for="option in options"
      :key="option.letter"
      class="flex items-start gap-2 rounded-4 border px-2.5 py-1.5"
      :class="rowClass(option)"
    >
      <span
        class="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full text-p-xs font-medium"
        :class="letterClass(option)"
      >
        {{ option.letter.toUpperCase() }}
      </span>
      <div
        v-if="hasRichContent(option.text)"
        class="rich-text min-w-0 flex-1 text-p-sm text-ink-gray-8 [&_img]:max-h-48"
        v-html="sanitizeHtml(option.text)"
      />
      <span v-else class="flex-1 text-p-sm italic text-ink-gray-4">
        {{ t('list.emptyValue') }}
      </span>
      <Badge
        v-if="option.isSelected"
        :label="selectedIsCorrect(option) ? '✓' : '✗'"
        :theme="selectedIsCorrect(option) ? 'green' : 'red'"
        variant="subtle"
      />
      <Badge
        v-else-if="option.isCorrect"
        label="✓"
        theme="green"
        variant="subtle"
      />
    </div>
  </div>
</template>
