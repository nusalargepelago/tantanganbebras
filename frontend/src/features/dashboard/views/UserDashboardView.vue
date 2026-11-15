<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge } from 'frappe-ui'

import PanelCard from '@/shared/components/PanelCard.vue'
import { useAuthStore } from '@/features/auth/store'

const auth = useAuthStore()
const { t } = useI18n()

const user = computed(() => auth.user)
</script>

<template>
  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <PanelCard class="space-y-1">
      <p class="text-p-sm text-ink-gray-5">{{ t('dash.welcomeBack') }}</p>
      <div class="text-xl-semibold text-ink-gray-8">
        {{ user?.fullName || user?.username }}
      </div>
      <p class="text-p-sm text-ink-gray-5">{{ user?.email }}</p>
    </PanelCard>

    <PanelCard :title="t('dash.roles')">
      <div class="mt-3 flex flex-wrap gap-2">
        <Badge v-if="user?.appRole" :label="user.appRole" theme="blue" />
        <Badge v-for="role in user?.roles ?? []" :key="role" :label="role" />
        <p
          v-if="!user?.appRole && !user?.roles?.length"
          class="text-p-sm text-ink-gray-5"
        >
          {{ t('dash.noRoles') }}
        </p>
      </div>
    </PanelCard>
  </div>
</template>
