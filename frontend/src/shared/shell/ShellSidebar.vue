<script setup lang="ts">
import { Sidebar, SidebarCollapseToggle, SidebarItem, SidebarSection } from 'frappe-ui'

import type { ShellNavItem } from './types'

defineProps<{
  items: ShellNavItem[]
  sectionLabel?: string
}>()

const collapsed = defineModel<boolean>('collapsed', { default: false })
</script>

<template>
  <Sidebar v-model:collapsed="collapsed" class="border-r">
    <!-- The header is app-specific (brand, avatar menu), so it arrives through
         the slot and lands as the first Sidebar child. -->
    <slot name="header" />

    <div class="flex-1 overflow-y-auto space-y-0.5 px-2 pb-2">
      <SidebarSection :label="sectionLabel">
        <SidebarItem
          v-for="item in items"
          :key="item.key"
          :label="item.label"
          :icon="item.icon"
          :route="item.route"
          :active="item.active"
        />
      </SidebarSection>
    </div>

    <div class="px-2 pb-2">
      <SidebarCollapseToggle />
    </div>
  </Sidebar>
</template>
