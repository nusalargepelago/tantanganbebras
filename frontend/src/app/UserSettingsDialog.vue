<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Avatar,
  Button,
  SettingsBody,
  SettingsContent,
  SettingsDialog,
  SettingsHeader,
  SettingsNavGroup,
  SettingsNavItem,
  SettingsPanel,
  Select,
  SettingsRow,
  SettingsSidebar,
} from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import { openCatalog } from '@/app/tour/store'
import ThemeSwitcher from './ThemeSwitcher.vue'

const open = defineModel<boolean>('open', { default: false })
const activeTab = defineModel<string>('tab', { default: 'profile' })

const emit = defineEmits<{ logout: [] }>()

const { t, locale } = useI18n()
const auth = useAuthStore()

const user = computed(() => auth.user)
const displayName = computed(() => user.value?.fullName || user.value?.email || '')

const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Bahasa Indonesia', value: 'id' },
]

const language = computed({
  get: () => locale.value,
  set: (value: string | number | null) => {
    if (typeof value === 'string') locale.value = value
  },
})

function onLogout() {
  open.value = false
  emit('logout')
}

function openGuide() {
  open.value = false
  openCatalog()
}

const memberSince = computed(() => {
  const created = user.value?.createdOn
  if (!created) return '—'
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(
    new Date(created),
  )
})
</script>

<template>
  <SettingsDialog v-model:open="open" v-model:tab="activeTab">
    <template #title>{{ t('settings.title') }}</template>

    <SettingsSidebar>
      <SettingsNavGroup :label="t('settings.nav.user')">
        <SettingsNavItem value="profile">
          <template #prefix>
            <Avatar size="xs" :label="displayName" />
          </template>
          {{ t('settings.profile.title') }}
        </SettingsNavItem>
        <SettingsNavItem value="preferences">
          <template #prefix>
            <span class="lucide-sliders-horizontal size-4 text-ink-gray-6" />
          </template>
          {{ t('settings.preferences.title') }}
        </SettingsNavItem>
      </SettingsNavGroup>
    </SettingsSidebar>

    <SettingsContent class="settings-content">
      <SettingsPanel value="profile">
        <SettingsHeader class="settings-header" :title="t('settings.profile.title')">
          <template #actions>
            <Button
              variant="ghost"
              icon-left="lucide-x"
              :aria-label="t('shared.close')"
              class="sm:hidden"
              @click="open = false"
            />
          </template>
        </SettingsHeader>
        <SettingsBody class="settings-body">
          <div class="flex items-center gap-4 pt-6">
            <Avatar size="xl" :label="displayName" />
            <div class="min-w-0">
              <div class="truncate text-base-medium text-ink-gray-8">
                {{ displayName }}
              </div>
              <p class="truncate text-p-sm text-ink-gray-5">{{ user?.email }}</p>
            </div>
          </div>

          <div class="mt-8 divide-y divide-outline-gray-1">
            <SettingsRow :title="t('settings.profile.fullName')">
              <span class="text-base text-ink-gray-6">{{ user?.fullName || '—' }}</span>
            </SettingsRow>
            <SettingsRow :title="t('settings.profile.email')">
              <span class="text-base text-ink-gray-6">{{ user?.email || '—' }}</span>
            </SettingsRow>
            <SettingsRow :title="t('settings.profile.username')">
              <span class="text-base text-ink-gray-6">{{ user?.username || '—' }}</span>
            </SettingsRow>
            <SettingsRow :title="t('settings.profile.role')">
              <span class="text-base capitalize text-ink-gray-6">
                {{ user?.appRole || '—' }}
              </span>
            </SettingsRow>
            <SettingsRow :title="t('settings.profile.memberSince')">
              <span class="text-base text-ink-gray-6">{{ memberSince }}</span>
            </SettingsRow>
          </div>

          <div
            class="mt-8 flex flex-col gap-2 border-t border-outline-gray-1 pt-4 sm:hidden"
          >
            <Button
              variant="outline"
              theme="gray"
              icon-left="lucide-compass"
              :label="t('tour.menu')"
              @click="openGuide"
            />
            <Button
              :label="t('menu.logout')"
              icon-left="lucide-log-out"
              theme="red"
              variant="subtle"
              @click="onLogout"
            />
          </div>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="preferences">
        <SettingsHeader class="settings-header" :title="t('settings.preferences.title')">
          <template #actions>
            <Button
              variant="ghost"
              icon-left="lucide-x"
              :aria-label="t('shared.close')"
              class="sm:hidden"
              @click="open = false"
            />
          </template>
        </SettingsHeader>
        <SettingsBody class="settings-body">
          <div class="mt-8 divide-y divide-outline-gray-1">
            <div class="flex flex-col gap-3 py-3.5 sm:flex-row sm:items-center sm:gap-8">
              <div class="min-w-0 flex-1">
                <div class="text-base-medium leading-tighter text-ink-gray-8">
                  {{ t('settings.preferences.theme') }}
                </div>
                <div class="mt-1 text-base leading-5 text-ink-gray-6">
                  {{ t('settings.preferences.themeDescription') }}
                </div>
              </div>
              <div class="sm:shrink-0">
                <ThemeSwitcher />
              </div>
            </div>

            <div class="flex flex-col gap-3 py-3.5 sm:flex-row sm:items-center sm:gap-8">
              <div class="min-w-0 flex-1">
                <div class="text-base-medium leading-tighter text-ink-gray-8">
                  {{ t('settings.preferences.language') }}
                </div>
                <div class="mt-1 text-base leading-5 text-ink-gray-6">
                  {{ t('settings.preferences.languageDescription') }}
                </div>
              </div>
              <div class="sm:shrink-0">
                <Select
                  v-model="language"
                  :options="languageOptions"
                  :aria-label="t('settings.preferences.language')"
                  class="w-full sm:w-44"
                />
              </div>
            </div>
          </div>
        </SettingsBody>
      </SettingsPanel>
    </SettingsContent>
  </SettingsDialog>
</template>

<style scoped>
/*
 * frappe-ui paints the settings tab shell at 100vw inside a card the dialog
 * insets by 1rem a side, and hardcodes a 4.4rem panel inset meant for desktop.
 * On a phone that leaves ~250px of content and clips the panel's right edge, so
 * below sm the panel is clamped to the card and the inset becomes 1.25rem.
 */
@media (max-width: 639px) {
  .settings-content {
    width: calc(100vw - 2rem);
  }

  .settings-header {
    padding-inline: 1.25rem;
    padding-top: 1.5rem;
  }

  .settings-body :deep([data-slot='scroll-area-viewport']) {
    padding-inline: 1.25rem;
  }
}
</style>
