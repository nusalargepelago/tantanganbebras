<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRouter, type RouteLocationRaw } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { BottomSheet, Icon } from 'frappe-ui'
import { List, ListCell, ListRow } from 'frappe-ui/list'

import { useMediaQuery } from '../composables/useMediaQuery'
import { mobileMenuOpen } from './mobile-menu'
import type { ShellNavItem } from './types'

const props = defineProps<{
  items: ShellNavItem[]
  title: string
}>()

const emit = defineEmits<{
  logout: []
}>()

const router = useRouter()
const { t } = useI18n()
const isDesktop = useMediaQuery('(min-width: 640px)')

// An imported ref is not assignable in compiled templates, so the sheet binds
// through a writable computed instead.
const open = computed({
  get: () => mobileMenuOpen.value,
  set: (value: boolean) => {
    mobileMenuOpen.value = value
  },
})

// The sheet unmounts above the breakpoint; drop the flag so it does not pop
// back open when the viewport returns to mobile.
watch(isDesktop, (desktop) => {
  if (desktop) mobileMenuOpen.value = false
})

function go(item: ShellNavItem) {
  mobileMenuOpen.value = false
  void router.push(item.route as RouteLocationRaw)
}

function onLogout() {
  mobileMenuOpen.value = false
  emit('logout')
}
</script>

<template>
  <BottomSheet v-if="!isDesktop" v-model:open="open" :title="title">
    <div class="px-2 pb-4">
      <p class="px-3 pb-1 pt-3 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
        {{ t('menu.section') }}
      </p>
      <List>
        <ListRow
          v-for="item in props.items"
          :key="item.key"
          :active="item.active"
          class="h-11 cursor-pointer rounded-5"
          @click="go(item)"
        >
          <ListCell>
            <Icon :icon="item.icon" class="size-5 shrink-0 text-ink-gray-5" />
          </ListCell>
          <ListCell>
            <span class="truncate text-base text-ink-gray-8">{{ item.label }}</span>
          </ListCell>
        </ListRow>
      </List>

      <div class="mt-2 border-t border-outline-gray-2 pt-2">
        <List>
          <ListRow class="h-11 cursor-pointer rounded-5" @click="onLogout">
            <ListCell>
              <Icon icon="lucide-log-out" class="size-5 shrink-0 text-ink-gray-5" />
            </ListCell>
            <ListCell>
              <span class="truncate text-base text-ink-gray-8">{{ t('menu.logout') }}</span>
            </ListCell>
          </ListRow>
        </List>
      </div>
    </div>
  </BottomSheet>
</template>
