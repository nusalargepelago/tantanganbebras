<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  ErrorMessage,
  FormControl,
  Select,
  toast,
} from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useStudentStore } from '../store'
import { categoryOptions, statusOptions } from '@/shared/labels'

const route = useRoute()
const router = useRouter()
const store = useStudentStore()
const { t } = useI18n()

const categorySelect = computed(() => categoryOptions())
const statusSelect = computed(() => statusOptions())

const userId = computed(() => (route.name === 'StudentEdit' ? (route.params.userId as string) : null))
const isEdit = computed(() => !!userId.value)

const form = reactive({
  firstName: '',
  lastName: '',
  email: '',
  username: '',
  password: '',
  category: 'cub',
  school: '',
  city: '',
  country: 'Indonesia',
  status: 'Inactive',
})
const snapshot = ref('')
const submitting = ref(false)
const loadError = ref('')

const isDirty = computed(() => JSON.stringify(form) !== snapshot.value)
const canSave = computed(() => isDirty.value && !submitting.value)

const disabled = computed(
  () =>
    submitting.value ||
    !form.firstName.trim() ||
    !form.lastName.trim() ||
    !form.email.trim() ||
    !form.username.trim() ||
    (!isEdit.value && form.password.length < 6),
)

async function load() {
  if (userId.value) {
    const student = await store.get(userId.value)
    if (!student) {
      loadError.value = store.error || t('student.loadFailed')
      return
    }
    Object.assign(form, {
      firstName: student.firstName,
      lastName: student.lastName,
      email: student.email,
      username: student.username,
      password: '',
      category: student.category,
      school: student.school ?? '',
      city: student.city ?? '',
      country: student.country ?? 'Indonesia',
      status: student.status,
    })
  }
  snapshot.value = JSON.stringify(form)
}

async function onSubmit() {
  if (disabled.value || !isDirty.value) return
  submitting.value = true
  let saved
  if (isEdit.value) {
    const payload: Record<string, unknown> = {
      firstName: form.firstName.trim(),
      lastName: form.lastName.trim(),
      email: form.email.trim(),
      category: form.category,
      school: form.school.trim() || null,
      city: form.city.trim() || null,
      country: form.country.trim() || null,
      status: form.status,
    }
    if (form.password) payload.password = form.password
    saved = await store.update(userId.value!, payload)
  } else {
    saved = await store.create({
      firstName: form.firstName.trim(),
      lastName: form.lastName.trim(),
      email: form.email.trim(),
      username: form.username.trim(),
      password: form.password,
      category: form.category,
      school: form.school.trim() || undefined,
      city: form.city.trim() || undefined,
      country: form.country.trim() || undefined,
      status: form.status,
    })
  }
  submitting.value = false

  if (!saved) {
    toast.error(store.error || t('student.saveFailed'))
    return
  }
  toast.success(isEdit.value ? t('student.updatedToast') : t('student.createdToast'))
  router.push({ name: 'StudentDetail', params: { userId: saved.userId } })
}

function onCancel() {
  if (isEdit.value) {
    router.push({ name: 'StudentDetail', params: { userId: userId.value } })
  } else {
    router.push({ name: 'StudentList' })
  }
}

onMounted(load)
</script>

<template>
  <AppPageHeader
    :title="isEdit ? t('route.StudentEdit.title') : t('route.StudentNew.title')"
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
        :disabled="!canSave || disabled"
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
        :disabled="!canSave || disabled"
        @click="onSubmit"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <ErrorMessage v-if="loadError" :message="loadError" />

    <section class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('form.identity') }}</h2>
      <div class="grid gap-4 sm:grid-cols-2">
        <FormControl
          v-model="form.firstName"
          :label="t('field.firstName')"
          placeholder="Budi"
          required
        />
        <FormControl
          v-model="form.lastName"
          :label="t('field.lastName')"
          placeholder="Santoso"
          required
        />
      </div>
      <FormControl
        v-model="form.email"
        type="email"
        :label="t('field.email')"
        placeholder="budi@example.com"
        required
      />
      <FormControl
        v-model="form.username"
        :label="t('field.username')"
        placeholder="budi"
        :description="isEdit ? undefined : t('form.usernameMin')"
        :disabled="isEdit"
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
    </section>

    <section class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('form.details') }}</h2>
      <div class="grid gap-4 sm:grid-cols-2">
        <Select v-model="form.category" :label="t('field.category')" :options="categorySelect" />
        <Select v-model="form.status" :label="t('field.status')" :options="statusSelect" />
      </div>
      <div class="grid gap-4 sm:grid-cols-2">
        <FormControl v-model="form.school" :label="t('field.school')" placeholder="SMPN 1" />
        <FormControl v-model="form.city" :label="t('field.city')" placeholder="Bandung" />
      </div>
      <FormControl v-model="form.country" :label="t('field.country')" placeholder="Indonesia" />
    </section>
  </div>
</template>
