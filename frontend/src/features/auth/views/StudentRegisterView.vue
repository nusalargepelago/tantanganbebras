<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Alert, Button, ErrorMessage, FormControl, Select } from 'frappe-ui'

import { useAuthStore } from '../store'
import { categoryOptions } from '@/shared/labels'

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()

const categorySelect = computed(() => categoryOptions())

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
})
const submitting = ref(false)

const disabled = computed(
  () =>
    submitting.value ||
    !form.firstName.trim() ||
    !form.lastName.trim() ||
    !form.email.trim() ||
    !form.username.trim() ||
    form.password.length < 6,
)

async function onSubmit() {
  if (disabled.value) return
  submitting.value = true
  const ok = await auth.studentRegister({
    firstName: form.firstName.trim(),
    lastName: form.lastName.trim(),
    email: form.email.trim(),
    username: form.username.trim(),
    password: form.password,
    category: form.category,
    school: form.school.trim() || undefined,
    city: form.city.trim() || undefined,
    country: form.country.trim() || undefined,
  })
  submitting.value = false
  if (ok) await router.replace('/')
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-surface-base p-4 text-ink-gray-8">
    <div class="w-full max-w-md rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6">
      <form class="space-y-4" @submit.prevent="onSubmit">
        <div class="flex flex-col items-center gap-1.5 text-center">
          <h1 class="text-2xl-semibold text-ink-gray-8">{{ t('auth.studentRegister.title') }}</h1>
          <p class="text-p-sm text-ink-gray-5">Tantangan Bebras</p>
        </div>

        <Alert
          theme="amber"
          icon="lucide-info"
          :title="t('auth.studentRegister.adminActivate')"
        />

        <ErrorMessage v-if="auth.error" :message="auth.error" />

        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.firstName"
            :label="t('auth.studentRegister.firstName')"
            placeholder="Budi"
            required
          />
          <FormControl
            v-model="form.lastName"
            :label="t('auth.studentRegister.lastName')"
            placeholder="Santoso"
            required
          />
        </div>
        <FormControl
          v-model="form.email"
          type="email"
          :label="t('auth.field.email')"
          placeholder="budi@example.com"
          required
        />
        <FormControl
          v-model="form.username"
          :label="t('auth.field.username')"
          placeholder="budi"
          :description="t('auth.studentRegister.usernameMin')"
          required
        />
        <FormControl
          v-model="form.password"
          type="password"
          :label="t('auth.field.password')"
          placeholder="••••••••"
          :description="t('auth.studentRegister.passwordMin')"
          required
        />
        <Select v-model="form.category" :label="t('auth.studentRegister.category')" :options="categorySelect" />

        <div class="grid gap-3 sm:grid-cols-2">
          <FormControl
            v-model="form.school"
            :label="t('auth.studentRegister.school')"
            placeholder="SMPN 1"
          />
          <FormControl v-model="form.city" :label="t('auth.studentRegister.city')" placeholder="Bandung" />
        </div>
        <FormControl
          v-model="form.country"
          :label="t('auth.studentRegister.country')"
          placeholder="Indonesia"
        />

        <Button
          type="submit"
          variant="solid"
          theme="gray"
          icon-left="lucide-user-plus"
          :label="t('auth.createAccount')"
          :loading="submitting"
          :disabled="disabled"
        />

        <p class="text-center text-p-sm text-ink-gray-5">
          {{ t('auth.haveAccount') }}
          <router-link :to="{ name: 'StudentLogin' }" class="text-ink-blue-link">
            {{ t('auth.signIn') }}
          </router-link>
        </p>
      </form>
    </div>
  </div>
</template>
