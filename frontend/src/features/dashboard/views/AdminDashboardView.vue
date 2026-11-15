<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Spinner } from 'frappe-ui'

import { useAccountStore } from '@/features/account/store'
import { useAuthStore } from '@/features/auth/store'
import { getErrorMessage } from '@/shared/api'

const auth = useAuthStore()
const account = useAccountStore()
const router = useRouter()
const { t } = useI18n()

const user = computed(() => auth.user)
const userTotal = ref<number | null>(null)
const statsError = ref('')
const statsReady = ref(false)

onMounted(async () => {
  try {
    const [total] = await Promise.all([
      account.fetchUserTotal(),
      auth.fetchRegistrationMode(true),
    ])
    userTotal.value = total
  } catch (e) {
    statsError.value = getErrorMessage(e, t('dash.loadStatsFailed'))
  } finally {
    statsReady.value = true
  }
})
</script>

<template>
  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <div class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <p class="text-p-sm text-ink-gray-5">{{ t('dash.welcomeBack') }}</p>
      <div class="text-xl-semibold text-ink-gray-8">
        {{ user?.fullName || user?.username }}
      </div>
      <p class="text-p-sm text-ink-gray-5">{{ user?.email }}</p>
    </div>

    <Spinner v-if="!statsReady" class="mx-auto" />

    <template v-else>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
          <div class="text-p-sm text-ink-gray-5">{{ t('dash.totalUsers') }}</div>
          <div class="mt-2 text-2xl-semibold text-ink-gray-8">
            {{ userTotal ?? '—' }}
          </div>
        </div>

        <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
          <div class="text-p-sm text-ink-gray-5">{{ t('dash.registration') }}</div>
          <div class="mt-2">
            <Badge
              :label="
                auth.registrationMode === 'closed'
                  ? t('dash.registrationClosed')
                  : t('dash.registrationOpen')
              "
              :theme="auth.registrationMode === 'closed' ? 'gray' : 'green'"
            />
          </div>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <div>
          <div class="text-base-medium text-ink-gray-8">{{ t('dash.adminConsole') }}</div>
          <p class="text-p-sm text-ink-gray-5">{{ t('dash.adminConsoleHint') }}</p>
        </div>
        <Button
          variant="solid"
          theme="gray"
          icon-left="lucide-users"
          :label="t('dash.manageUsers')"
          @click="router.push({ name: 'Users' })"
        />
      </div>

      <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <div class="text-base-medium text-ink-gray-8">{{ t('dash.roles') }}</div>
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
      </div>
    </template>
    <ErrorMessage v-if="statsError" :message="statsError" />
  </div>
</template>
