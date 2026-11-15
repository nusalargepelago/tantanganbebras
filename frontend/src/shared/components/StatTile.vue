<script setup lang="ts">
/**
 * Metric tile: label + prominent value. Nullish values render as a dash;
 * the default slot overrides the value row entirely.
 */
defineProps<{
  label: string
  value?: string | number | null
}>()
</script>

<template>
  <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
    <div class="text-p-sm text-ink-gray-5">{{ label }}</div>
    <div class="mt-2 text-2xl-semibold text-ink-gray-8">
      <slot>{{ value ?? '—' }}</slot>
    </div>
  </div>
</template>
