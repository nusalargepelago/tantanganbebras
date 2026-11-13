<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ErrorMessage, Spinner } from 'frappe-ui'

const { t } = useI18n()

withDefaults(
  defineProps<{
    loading?: boolean
    error?: string | null
    empty?: boolean
    icon?: string
    emptyMessage?: string
  }>(),
  {
    loading: false,
    error: null,
    empty: false,
    icon: 'lucide-inbox',
  },
)
</script>

<template>
  <div v-if="loading" class="flex justify-center py-10">
    <Spinner />
  </div>

  <ErrorMessage v-else-if="error" :message="error" />

  <div
    v-else-if="empty"
    class="flex flex-col items-center gap-2 py-10 text-center"
  >
    <span :class="[icon, 'size-8 text-ink-gray-4']" aria-hidden="true" />
    <p class="text-p-sm text-ink-gray-5">
      {{ emptyMessage ?? t('shared.noResults') }}
    </p>
    <slot name="action" />
  </div>

  <slot v-else />
</template>
