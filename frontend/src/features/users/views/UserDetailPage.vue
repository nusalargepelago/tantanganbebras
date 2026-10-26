<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton, dialog, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { statusLabel } from '@/shared/labels'

import { useUsersStore } from '../store'

const route = useRoute()
const router = useRouter()
const store = useUsersStore()
const { t } = useI18n()

const userId = computed(() => route.params.id as string)
const user = computed(() => store.current)

async function load() {
  await store.get(userId.value)
}

function onResetPassword() {
  dialog.prompt({
    title: t('users.resetPassword'),
    message: t('users.resetMessage'),
    fields: [
      {
        name: 'password',
        label: t('users.resetFieldLabel'),
        type: 'text',
        validate: (value: string) => (value.length >= 6 ? undefined : t('form.passwordMin')),
      },
    ],
    onConfirm: async ({ values }) => {
      const updated = await store.update(userId.value, { password: values.password })
      if (!updated) throw new Error(store.error || t('users.resetFailed'))
      toast.success(t('users.resetToast'))
    },
  })
}

function onDelete() {
  dialog.danger({
    title: t('users.deleteTitle'),
    message: t('users.deleteMessage', { name: user.value?.fullName ?? '' }),
    onConfirm: async () => {
      const ok = await store.remove(userId.value)
      if (!ok) throw new Error(store.error || t('users.deleteFailed'))
      toast.success(t('users.deletedToast'))
      router.push({ name: 'UsersList' })
    },
  })
}

onMounted(load)
</script>

<template>
  <AppPageHeader :title="user?.fullName || t('route.UserDetail.title')">
    <template #actions>
      <Button
        variant="outline"
        theme="gray"
        icon-left="lucide-key"
        :label="t('users.resetPassword')"
        @click="onResetPassword"
      />
      <Button
        variant="outline"
        theme="gray"
        :label="t('list.edit')"
        :route="{ name: 'UserEdit', params: { id: userId } }"
      />
      <Button
        variant="outline"
        theme="red"
        icon-left="lucide-trash-2"
        :label="t('list.delete')"
        @click="onDelete"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-key"
        :label="t('users.resetPassword')"
        @click="onResetPassword"
      />
      <Button
        variant="ghost"
        icon="lucide-pencil"
        :label="t('list.edit')"
        :route="{ name: 'UserEdit', params: { id: userId } }"
      />
      <Button
        variant="ghost"
        icon="lucide-trash-2"
        :label="t('list.delete')"
        @click="onDelete"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <Skeleton v-if="store.currentLoading" class="h-40" />
    <ErrorMessage v-else-if="store.error" :message="store.error" />

    <template v-else-if="user">
      <div class="flex flex-wrap items-center gap-2">
        <Badge :label="user.appRole" variant="subtle" />
        <Badge
          :label="user.isActive ? 'Active' : 'Inactive'"
          :theme="user.isActive ? 'green' : 'gray'"
          variant="subtle"
        />
      </div>

      <div class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <h1 class="text-2xl-semibold text-ink-gray-8">{{ user.fullName }}</h1>
        <p class="text-p-sm text-ink-gray-5">{{ user.email }}</p>
        <p class="text-p-sm text-ink-gray-5">@{{ user.username }}</p>
      </div>

      <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <h2 class="text-xl-semibold text-ink-gray-8">{{ t('detail.account') }}</h2>
        <dl class="mt-3 grid gap-2 text-p-sm sm:grid-cols-2">
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('detail.userId') }}</dt>
            <dd class="text-ink-gray-8">{{ user.id }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('users.role') }}</dt>
            <dd class="text-ink-gray-8">{{ user.appRole }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('list.status') }}</dt>
            <dd class="text-ink-gray-8">{{ statusLabel(user.isActive ? 'Active' : 'Inactive') }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('users.created') }}</dt>
            <dd class="text-ink-gray-8">
              {{ user.createdOn ? new Date(user.createdOn).toLocaleString() : '—' }}
            </dd>
          </div>
        </dl>
      </div>
    </template>
  </div>
</template>
