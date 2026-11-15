<script setup lang="ts">
import { useBrandLogo } from '@/shared/brand'

withDefaults(
  defineProps<{
    size?: 'md' | 'lg' | 'fill'
    alt?: string
  }>(),
  { size: 'md', alt: '' },
)

const sizeClass = {
  md: 'size-12 rounded-6',
  lg: 'size-14 rounded-6',
  fill: 'h-full w-full',
} as const

const { logoSrc, onLogoError } = useBrandLogo()
</script>

<template>
  <div class="overflow-hidden bg-surface-gray-2" :class="sizeClass[size]">
    <img
      v-if="logoSrc"
      :src="logoSrc"
      :alt="alt"
      class="h-full w-full object-cover"
      @error="onLogoError"
    />
    <slot v-else />
  </div>
</template>
