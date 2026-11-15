<script setup lang="ts">
defineProps<{ label: string }>()

const emit = defineEmits<{ click: [event: MouseEvent] }>()
</script>

<template>
  <button
    type="button"
    class="absolute inset-0 sm:rounded-5"
    :aria-label="label"
    @click="emit('click', $event)"
  />
</template>
