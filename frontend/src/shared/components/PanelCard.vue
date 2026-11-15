<script setup lang="ts">
/**
 * Bordered surface section — the standard panel container. Pass `title` for
 * the common case; anything richer goes through the slots.
 */
defineProps<{
  title?: string
}>()
</script>

<template>
  <section class="min-w-0 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
    <div
      v-if="title || $slots.actions"
      class="flex flex-wrap items-center justify-between gap-3"
    >
      <h2 class="text-base-medium text-ink-gray-8">{{ title }}</h2>
      <div v-if="$slots.actions" class="ml-auto flex items-center gap-2">
        <slot name="actions" />
      </div>
    </div>
    <slot />
  </section>
</template>
