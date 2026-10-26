<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Select, TextInput, type SelectOptionValue } from 'frappe-ui'

const { t } = useI18n()

const search = defineModel<string>('search', { default: '' })
const perPage = defineModel<number>('perPage', { default: 20 })

const props = withDefaults(
  defineProps<{
    placeholder?: string
    perPageOptions?: { label: string; value: number }[]
    showPerPage?: boolean
  }>(),
  {
    showPerPage: true,
  },
)

const defaultPerPageOptions = computed(() => [
  { label: t('shared.perPage', { n: 10 }), value: 10 },
  { label: t('shared.perPage', { n: 20 }), value: 20 },
  { label: t('shared.perPage', { n: 50 }), value: 50 },
])

function onPerPage(value: SelectOptionValue | null | undefined) {
  if (typeof value === 'number') perPage.value = value
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <TextInput
      v-model="search"
      type="search"
      :placeholder="props.placeholder ?? t('shared.search')"
      class="w-full min-w-0 sm:w-64"
    />
    <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
      <slot />
      <Select
        v-if="showPerPage"
        :model-value="perPage"
        :options="props.perPageOptions ?? defaultPerPageOptions"
        class="ml-auto w-36"
        @update:model-value="onPerPage"
      />
    </div>
  </div>
</template>
