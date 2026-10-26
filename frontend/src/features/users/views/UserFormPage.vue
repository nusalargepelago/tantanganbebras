<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, FormControl, Select, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useUsersStore } from '../store'

const route = useRoute()
const router = useRouter()
const store = useUsersStore()
const { t } = useI18n()

const roleSelect = computed(() => [
  { label: t('users.roleUser'), value: 'user' },
  { label: t('users.roleAdmin'), value: 'admin' },
])

const userId = computed(() => (route.name === 'UserEdit' ? (route.params.id as string) : null))
const isEdit = computed(() => !!userId.value)

const form = reactive({ fullName: '', email: '', password: '', appRole: 'user' })
const snapshot = ref('')
const submitting = ref(false)
const loadError = ref('')

const isDirty = computed(() => JSON.stringify(form) !== snapshot.value)
const disabled = computed(
  () =>
    submitting.value ||
    !form.fullName.trim() ||
    (!isEdit.value && !form.email.trim()) ||
    (!isEdit.value && form.password.length < 6),
)

async function load() {
  if (userId.value) {
    const user = await store.get(userId.value)
    if (!user) {
      loadError.value = store.error || t('users.loadFailed')
      return
    }
    Object.assign(form, {
      fullName: user.fullName,
      email: user.email,
      password: '',
      appRole: user.appRole || 'user',
    })
  }
  snapshot.value = JSON.stringify(form)
}

async function onSubmit() {
  if (disabled.value || !isDirty.value) return
  submitting.value = true
  let saved
  if (isEdit.value) {
    const payload: Record<string, unknown> = { fullName: form.fullName.trim(), appRole: form.appRole }
    if (form.password) payload.password = form.password
    saved = await store.update(userId.value!, payload)
  } else {
    saved = await store.create({
      fullName: form.fullName.trim(),
      email: form.email.trim(),
      password: form.password,
      appRole: form.appRole,
    })
  }
  submitting.value = false

  if (!saved) {
    toast.error(store.error || t('users.saveFailed'))
    return
  }
  toast.success(isEdit.value ? t('users.updatedToast') : t('users.createdToast'))
  router.push({ name: 'UsersList' })
}

function onCancel() {
  router.push({ name: 'UsersList' })
}

onMounted(load)
</script>

<template>
  <AppPageHeader
    :title="isEdit ? t('route.UserEdit.title') : t('route.UserNew.title')"
  >
    <template #leading>
      <Badge v-if="isDirty" :label="t('form.unsaved')" theme="amber" variant="subtle" />
    </template>
    <template #actions>
      <Button variant="outline" theme="gray" :label="t('shared.cancel')" @click="onCancel" />
      <Button
        variant="solid"
        :label="t('shared.save')"
        :loading="submitting"
        :disabled="!isDirty || disabled"
        @click="onSubmit"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-x"
        :label="t('shared.cancel')"
        @click="onCancel"
      />
      <Button
        variant="ghost"
        icon="lucide-check"
        :label="t('shared.save')"
        :loading="submitting"
        :disabled="!isDirty || disabled"
        @click="onSubmit"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <ErrorMessage v-if="loadError" :message="loadError" />

    <section class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <FormControl
        v-model="form.fullName"
        :label="t('field.fullName')"
        placeholder="Jane Doe"
        required
      />
      <FormControl
        v-if="!isEdit"
        v-model="form.email"
        type="email"
        :label="t('field.email')"
        placeholder="jane@example.com"
        required
      />
      <FormControl
        v-model="form.password"
        type="password"
        :label="isEdit ? t('field.newPasswordOptional') : t('field.password')"
        placeholder="••••••••"
        :description="isEdit ? undefined : t('form.passwordMin')"
        :required="!isEdit"
      />
      <Select v-model="form.appRole" :label="t('users.role')" :options="roleSelect" />
    </section>
  </div>
</template>
