<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Avatar,
  BottomSheet,
  DesktopShell,
  MobileNav,
  MobileNavItem,
  MobileShell,
  Sidebar,
  SidebarCollapseToggle,
  SidebarHeader,
  SidebarItem,
  SidebarSection,
} from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import { openCatalog } from '@/app/tour/store'
import ForbiddenDialog from '@/shared/components/ForbiddenDialog.vue'
import { brand } from '@/shared/brand'
import { useFocusMode } from './focus-mode'
import { isNavActive, navFor, primaryNav } from './navigation'
import { mobileMenuOpen } from './mobile-menu'
import { useMediaQuery } from './useMediaQuery'
import ThemeSwitcher from './ThemeSwitcher.vue'
import UserSettingsDialog from './UserSettingsDialog.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { t } = useI18n()

const isFullscreen = computed(
  () => route.meta.fullscreen === true || route.query.fullscreen === '1',
)

const isDesktop = useMediaQuery('(min-width: 640px)')

const displayName = computed(() => auth.user?.fullName || auth.user?.email || '')

const sidebarCollapsed = ref(false)
const { active: focusMode } = useFocusMode()

const navFlags = computed(() => ({
  staff: auth.isStaff,
  student: auth.isStudent,
  admin: auth.isAdmin,
}))
const visibleNav = computed(() => navFor(navFlags.value))
const primaryTabs = computed(() => primaryNav(navFlags.value))

const sheetRowClass =
  'flex min-h-11 w-full items-center gap-3 rounded-6 px-3 text-p-sm transition'
const sheetRowActive = 'bg-surface-elevation-3 text-ink-gray-8 shadow-sm'
const sheetRowIdle = 'text-ink-gray-6 hover:bg-surface-gray-2'

// An imported ref is not assignable in compiled templates, so the sheet binds
// through a writable computed instead.
const sheetOpen = computed({
  get: () => mobileMenuOpen.value,
  set: (value: boolean) => {
    mobileMenuOpen.value = value
  },
})

function closeSheet() {
  mobileMenuOpen.value = false
}

// The sheet unmounts above the breakpoint; drop the flag so it does not pop
// back open when the viewport returns to mobile.
watch(isDesktop, (desktop) => {
  if (desktop) closeSheet()
})

const settingsOpen = ref(false)
const settingsTab = ref('profile')

function openSettings(tab: 'profile' | 'preferences' = 'profile') {
  settingsTab.value = tab
  settingsOpen.value = true
}

const headerMenu = computed(() => [
  {
    group: t('menu.theme'),
    options: [
      {
        label: t('menu.theme'),
        slots: { label: () => h(ThemeSwitcher) },
      },
    ],
  },
  { label: t('tour.menu'), icon: 'lucide-compass', onClick: openCatalog },
  {
    label: t('menu.settings'),
    icon: 'lucide-settings',
    onClick: () => openSettings(),
  },
  { label: t('menu.logout'), icon: 'lucide-log-out', onClick: onLogout },
])

async function onLogout() {
  await auth.logout()
  await router.replace('/login')
}
</script>

<template>
  <router-view v-if="isFullscreen" />

  <DesktopShell v-else-if="isDesktop" :scroll="route.meta.scroll !== false">
    <template #sidebar>
      <Sidebar v-if="!focusMode" v-model:collapsed="sidebarCollapsed" class="border-r">
        <SidebarHeader
          data-tour="student-guide-menu"
          :title="brand.name"
          :subtitle="displayName"
          :menu-items="headerMenu"
        />
        <div class="flex-1 overflow-y-auto space-y-0.5 px-2 pb-2">
          <SidebarSection :label="t('menu.section')">
            <SidebarItem
              v-for="item in visibleNav"
              :key="item.key"
              :label="t(item.labelKey)"
              :icon="item.icon"
              :route="item.route"
              :active="isNavActive(item, route.path)"
            />
          </SidebarSection>
        </div>
        <div class="px-2 pb-2">
          <SidebarCollapseToggle />
        </div>
      </Sidebar>
    </template>

    <router-view />
  </DesktopShell>

  <MobileShell v-else>
    <router-view />

    <template #nav>
      <MobileNav v-if="!focusMode">
        <MobileNavItem
          v-for="item in primaryTabs"
          :key="item.key"
          :label="t(item.labelKey)"
          :icon="item.icon"
          :route="item.route"
          :active="isNavActive(item, route.path)"
        />
        <!-- Wrapped so the tour can spotlight the avatar: MobileNavItem renders
             two root nodes, so a data-tour attr on it would not fall through. -->
        <div data-tour="student-guide-menu">
          <MobileNavItem
            :label="t('settings.profile.title')"
            :active="settingsOpen"
            @click="openSettings('profile')"
          >
            <template #default="{ active }">
              <Avatar
                :label="displayName"
                size="md"
                :class="active ? 'ring-2 ring-outline-gray-4' : ''"
              />
            </template>
          </MobileNavItem>
        </div>
      </MobileNav>
    </template>
  </MobileShell>

  <BottomSheet
    v-if="!isDesktop"
    v-model:open="sheetOpen"
    :title="t('menu.section')"
  >
    <nav class="space-y-0.5 px-3 pb-6" :aria-label="t('menu.section')">
      <RouterLink
        v-for="item in visibleNav"
        :key="`sheet-${item.key}`"
        :to="item.route"
        :class="[
          sheetRowClass,
          isNavActive(item, route.path) ? sheetRowActive : sheetRowIdle,
        ]"
        @click="closeSheet"
      >
        <span :class="[item.icon, 'size-5 shrink-0']" aria-hidden="true" />
        <span class="min-w-0 flex-1 truncate">{{ t(item.labelKey) }}</span>
      </RouterLink>
    </nav>
  </BottomSheet>

  <UserSettingsDialog
    v-model:open="settingsOpen"
    v-model:tab="settingsTab"
    @logout="onLogout"
  />
  <ForbiddenDialog />
</template>

<style scoped>
/*
 * MobileNav is a grid of equal columns, but MobileNavItem's button variant
 * sizes to its content while the link variant stretches. The avatar tab was
 * therefore ~37px wide inside a ~98px column, so the four tabs were not evenly
 * spaced. Stretching every item keeps the columns identical.
 */
:deep([data-slot='mobile-nav-item']) {
  width: 100%;
}
</style>
