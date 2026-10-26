<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton, dialog, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useStudentStore } from '../store'
import { categoryLabel, statusLabel } from '@/shared/labels'

const route = useRoute()
const router = useRouter()
const store = useStudentStore()
const { t } = useI18n()

const userId = computed(() => route.params.userId as string)
const student = computed(() => store.current)

async function load() {
  await store.get(userId.value)
}

async function onActivate() {
  const updated = await store.activate(userId.value)
  if (!updated) {
    toast.error(store.error || t('student.activateFailed'))
    return
  }
  toast.success(t('student.activatedToast'))
}

function onDelete() {
  dialog.danger({
    title: t('student.deleteTitle'),
    message: t('student.deleteMessage', {
      name: `${student.value?.firstName ?? ''} ${student.value?.lastName ?? ''}`.trim(),
    }),
    onConfirm: async () => {
      const ok = await store.softDelete(userId.value)
      if (!ok) throw new Error(store.error || 'Failed to delete student')
      toast.success(t('student.deletedToast'))
      router.push({ name: 'StudentList' })
    },
  })
}

onMounted(load)
</script>

<template>
  <AppPageHeader
    :title="student ? `${student.firstName} ${student.lastName}` : t('route.StudentDetail.title')"
  >
    <template #actions>
      <Button
        v-if="student && student.status === 'Inactive' && !student.disabled"
        variant="outline"
        theme="green"
        icon-left="lucide-circle-check"
        label="Activate"
        @click="onActivate"
      />
      <Button
        variant="outline"
        theme="gray"
        :label="t('list.edit')"
        :route="{ name: 'StudentEdit', params: { userId } }"
      />
      <Button
        v-if="student && !student.disabled"
        variant="outline"
        theme="red"
        icon-left="lucide-trash-2"
        :label="t('list.delete')"
        @click="onDelete"
      />
    </template>
    <template #mobile-actions>
      <Button
        v-if="student && student.status === 'Inactive' && !student.disabled"
        variant="ghost"
        icon="lucide-circle-check"
        label="Activate"
        @click="onActivate"
      />
      <Button
        variant="ghost"
        icon="lucide-pencil"
        :label="t('list.edit')"
        :route="{ name: 'StudentEdit', params: { userId } }"
      />
      <Button
        v-if="student && !student.disabled"
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

    <template v-else-if="student">
      <div class="flex flex-wrap items-center gap-2">
        <Badge :label="categoryLabel(student.category)" variant="subtle" />
        <Badge
          v-if="student.disabled"
          :label="t('list.deleted')"
          theme="red"
          variant="subtle"
        />
        <Badge
          v-else
          :label="statusLabel(student.status)"
          :theme="student.status === 'Active' ? 'green' : 'amber'"
          variant="subtle"
        />
      </div>

      <div class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <h1 class="text-2xl-semibold text-ink-gray-8">
          {{ student.firstName }} {{ student.lastName }}
        </h1>
        <p class="text-p-sm text-ink-gray-5">@{{ student.username }}</p>
      </div>

      <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <h2 class="text-xl-semibold text-ink-gray-8">{{ t('detail.info') }}</h2>
        <dl class="mt-3 grid gap-2 text-p-sm sm:grid-cols-2">
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.email') }}</dt>
            <dd class="min-w-0 break-words text-ink-gray-8">{{ student.email }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.category') }}</dt>
            <dd class="min-w-0 break-words text-ink-gray-8">{{ categoryLabel(student.category) }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.school') }}</dt>
            <dd class="min-w-0 break-words text-ink-gray-8">{{ student.school || '—' }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.city') }}</dt>
            <dd class="min-w-0 break-words text-ink-gray-8">{{ student.city || '—' }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.country') }}</dt>
            <dd class="min-w-0 break-words text-ink-gray-8">{{ student.country || '—' }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.status') }}</dt>
            <dd class="min-w-0 break-words text-ink-gray-8">{{ statusLabel(student.status) }}</dd>
          </div>
        </dl>
      </div>
    </template>
  </div>
</template>
