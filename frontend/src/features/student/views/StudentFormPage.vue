<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Combobox,
  ErrorMessage,
  FormControl,
  Select,
  Spinner,
  toast,
} from 'frappe-ui'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import { useAuthStore } from '@/features/auth/store'
import { useStudentStore } from '../store'
import { categoryOptions, statusOptions } from '@/shared/labels'
import { fetchSchools, schoolOptions, type SchoolItem } from '@/shared/masters'

const route = useRoute()
const router = useRouter()
const store = useStudentStore()
const auth = useAuthStore()
const { t } = useI18n()
const isTeacher = computed(() => auth.isTeacher)

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
  schoolId: null as string | null,
  status: 'Inactive',
})
const schools = ref<SchoolItem[]>([])
const schoolSelect = ref<{ label: string; value: string }[]>([])
const pickedSchool = computed(() => schools.value.find((s) => s.id === form.schoolId))
const snapshot = ref('')
const submitting = ref(false)
const loadError = ref('')
const gateReady = ref(false)

const isDirty = computed(() => JSON.stringify(form) !== snapshot.value)
const canSave = computed(() => isDirty.value && !submitting.value)

const disabled = computed(
  () =>
    submitting.value ||
    !form.firstName.trim() ||
    !form.lastName.trim() ||
    !form.email.trim() ||
    !form.username.trim() ||
    (!isEdit.value && form.password.length < 6) ||
    (!isTeacher.value && !form.schoolId),
)

async function load() {
  try {
    schools.value = await fetchSchools()
  } catch {
    loadError.value = t('student.schoolsLoadFailed')
    gateReady.value = true
    return
  } finally {
    schoolSelect.value = schoolOptions(schools.value)
  }
  if (!isEdit.value) {
    gateReady.value = true
    snapshot.value = JSON.stringify(form)
    return
  }
  const student = await store.get(userId.value!)
  if (!student) {
    loadError.value = store.error || t('student.loadFailed')
    gateReady.value = true
    return
  }
  if (student.schoolId && !schools.value.some((s) => s.id === student.schoolId)) {
    // The student's school was deactivated — it is hidden from the active
    // list, so surface it read-only as the current option.
    schools.value = [
      ...schools.value,
      {
        id: student.schoolId,
        name: student.school ? `${student.school} (${t('status.inactive')})` : student.schoolId,
        isActive: false,
        city: student.city ? { id: '', name: student.city } : null,
      },
    ]
    schoolSelect.value = schoolOptions(schools.value)
  }
  Object.assign(form, {
    firstName: student.firstName,
    lastName: student.lastName,
    email: student.email,
    username: student.username,
    password: '',
    category: student.category,
    schoolId: student.schoolId ?? null,
    status: student.status,
  })
  snapshot.value = JSON.stringify(form)
  gateReady.value = true
}

async function onSubmit() {
  if (disabled.value || !isDirty.value) return
  if (!isTeacher.value && !form.schoolId) return
  submitting.value = true
  // Teacher payloads omit schoolId/status — the backend pins the school
  // and forces Inactive for students a teacher creates.
  const schoolPart: Record<string, unknown> = isTeacher.value
    ? {}
    : { schoolId: form.schoolId, status: form.status }
  let saved
  if (isEdit.value) {
    const payload: Record<string, unknown> = {
      firstName: form.firstName.trim(),
      lastName: form.lastName.trim(),
      email: form.email.trim(),
      category: form.category,
      ...schoolPart,
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
      status: 'Inactive',
      ...schoolPart,
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

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
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
      <p v-if="isTeacher" class="text-p-sm text-ink-gray-5">
        {{ t('student.teacherStudentNote') }}
      </p>
      <div class="grid gap-4 sm:grid-cols-2">
        <Select v-model="form.category" :label="t('field.category')" :options="categorySelect" />
        <Select v-if="!isTeacher" v-model="form.status" :label="t('field.status')" :options="statusSelect" />
      </div>
      <template v-if="!isTeacher">
        <Combobox
          v-model="form.schoolId"
          :label="t('field.school')"
          :options="schoolSelect"
          :placeholder="t('shared.selectPlaceholder')"
          :required="true"
        />
        <dl class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-base px-3 py-2 text-p-sm">
          <div class="flex items-center justify-between gap-3">
            <dt class="text-ink-gray-5">{{ t('field.city') }}</dt>
            <dd class="truncate text-ink-gray-8">
              {{ pickedSchool?.city?.name ?? t('shared.selectSchoolFirst') }}
            </dd>
          </div>
          <div class="flex items-center justify-between gap-3">
            <dt class="text-ink-gray-5">{{ t('field.country') }}</dt>
            <dd class="text-ink-gray-8">Indonesia</dd>
          </div>
        </dl>
      </template>
    </section>
  </div>
</template>
