<script setup lang="ts">
import { MobileNav, MobileNavItem } from 'frappe-ui'

import type { ShellNavItem } from './types'

defineProps<{
  items: ShellNavItem[]
}>()
</script>

<template>
  <MobileNav>
    <MobileNavItem
      v-for="item in items"
      :key="item.key"
      :label="item.label"
      :icon="item.icon"
      :route="item.route"
      :active="item.active"
    />
    <!-- Extra tab, e.g. the avatar that opens the menu sheet. -->
    <slot />
  </MobileNav>
</template>

<style scoped>
/*
 * MobileNav is a grid of equal columns, but MobileNavItem's button variant
 * sizes to its content while the link variant stretches. An avatar tab is
 * therefore narrower than the link tabs, so the columns are not evenly
 * spaced. Stretching every item keeps the columns identical.
 */
:deep([data-slot='mobile-nav-item']) {
  width: 100%;
}
</style>
