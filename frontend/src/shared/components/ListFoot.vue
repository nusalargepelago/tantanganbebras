<script setup lang="ts">
import Pagination from './Pagination.vue'

withDefaults(
  defineProps<{
    total: number
    page: number
    perPage: number
    always?: boolean
  }>(),
  { always: true },
)

const emit = defineEmits<{
  'update:page': [page: number]
}>()
</script>

<template>
  <div
    class="mt-1 flex min-h-8 items-center justify-end rounded-b-6 bg-surface-gray-2 px-3 py-0.5"
  >
    <Pagination
      :always="always"
      align="end"
      :total="total"
      :page="page"
      :per-page="perPage"
      @update:page="emit('update:page', $event)"
    />
  </div>
</template>
