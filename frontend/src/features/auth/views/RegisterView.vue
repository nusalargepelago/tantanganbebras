<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, ErrorMessage, FormControl, toast } from 'frappe-ui'

import { useAuthStore } from '../store'
import { checkPassword, isPasswordValid, passwordRules } from '../validation'
import { brand } from '@/shared/brand'

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()

const fullName = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const submitting = ref(false)

const errorMessage = computed(() => auth.error)

const passwordChecks = computed(() => checkPassword(password.value))
const passwordValid = computed(() => isPasswordValid(password.value))

const disabled = computed(
  () =>
    submitting.value ||
    !fullName.value.trim() ||
    !username.value.trim() ||
    !email.value.trim() ||
    !passwordValid.value,
)

async function onSubmit() {
  if (disabled.value) return
  submitting.value = true
  const ok = await auth.register({
    fullName: fullName.value.trim(),
    username: username.value.trim().toLowerCase(),
    email: email.value.trim(),
    password: password.value,
  })
  submitting.value = false
  if (ok) {
    toast.success(t('auth.register.created', { name: auth.user?.fullName ?? auth.user?.email }))
    await router.replace('/')
  }
}
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-surface-base p-4 text-ink-gray-8"
  >
    <div class="w-full max-w-sm rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6">
      <form class="space-y-4" @submit.prevent="onSubmit">
        <div class="flex flex-col items-center gap-1.5 text-center">
          <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
            <span class="lucide-package size-6" aria-hidden="true" />
          </div>
          <h1 class="text-2xl-semibold text-ink-gray-8">{{ t('auth.createAccount') }}</h1>
          <p class="text-p-sm text-ink-gray-5">{{ brand.name }}</p>
        </div>

        <ErrorMessage v-if="errorMessage" :message="errorMessage" />

        <FormControl
          v-model="fullName"
          :label="t('auth.register.fullName')"
          placeholder="Abdullah"
          autocomplete="name"
          required
        />
        <FormControl
          v-model="username"
          :label="t('auth.field.username')"
          placeholder="abdulah"
          autocomplete="username"
          required
        />
        <FormControl
          v-model="email"
          type="email"
          :label="t('auth.field.email')"
          placeholder="abdulah@example.com"
          autocomplete="email"
          required
        />
        <FormControl
          v-model="password"
          type="password"
          :label="t('auth.field.password')"
          placeholder="••••••••"
          autocomplete="new-password"
          required
        />

        <ul v-if="password.length" class="space-y-1">
          <li
            v-for="rule in passwordRules"
            :key="rule.key"
            class="flex items-center gap-1.5 text-p-xs"
            :class="passwordChecks[rule.key] ? 'text-ink-green-6' : 'text-ink-gray-5'"
          >
            <span
              :class="passwordChecks[rule.key] ? 'lucide-check' : 'lucide-minus'"
              class="size-3"
              aria-hidden="true"
            />
            {{ t(rule.label) }}
          </li>
        </ul>

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
          <router-link :to="{ name: 'Login' }" class="text-ink-blue-link">
            {{ t('auth.signIn') }}
          </router-link>
        </p>
      </form>
    </div>
  </div>
</template>
