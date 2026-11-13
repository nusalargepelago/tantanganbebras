<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Button,
  Dialog,
  ErrorMessage,
  MultiSelect,
  Password,
  Select,
  Switch,
  TextInput,
  toast,
} from 'frappe-ui'

import { checkPassword, passwordRules } from '@/features/auth/validation'
import { useAccountStore, type AdminUser } from '../store'

const props = defineProps<{
  user: AdminUser | null
}>()

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{
  saved: []
}>()

const store = useAccountStore()
const { t } = useI18n()

const isCreate = computed(() => props.user === null)

const email = ref('')
const username = ref('')
const password = ref('')
const fullName = ref('')
const appRole = ref('user')
const isActive = ref(true)
const roleNames = ref<string[]>([])
const saving = ref(false)
const error = ref('')

function resetForm() {
  const user = props.user
  email.value = ''
  username.value = ''
  password.value = ''
  fullName.value = user?.fullName ?? ''
  appRole.value = user?.appRole ?? 'user'
  isActive.value = user?.isActive ?? true
  roleNames.value = [...(user?.roles ?? [])]
  error.value = ''
}

watch(() => props.user, resetForm, { immediate: true })
watch(open, (isOpen) => {
  if (isOpen) resetForm()
})

onMounted(() => store.fetchRoles())

const appRoleOptions = computed(() => [
  { label: t('account.roleUser'), value: 'user' },
  { label: t('account.roleAdmin'), value: 'admin' },
])

const passwordChecks = computed(() => checkPassword(password.value))

const roleOptions = computed(() =>
  store.roles.map((role) => ({ label: role.name, value: role.name })),
)

const actions = computed(() => [
  {
    label: t('shared.cancel'),
    variant: 'ghost' as const,
    theme: 'gray' as const,
    onClick: ({ close }: { close: () => void }) => close(),
  },
  {
    label: isCreate.value ? t('account.createUser') : t('account.saveChanges'),
    variant: 'solid' as const,
    loading: saving.value,
    onClick: async () => {
      await onSave()
    },
  },
])

async function onSave() {
  saving.value = true
  error.value = ''

  if (props.user) {
    const updated = await store.updateUser(props.user.id, {
      fullName: fullName.value.trim(),
      appRole: appRole.value,
      isActive: isActive.value,
      roleNames: [...roleNames.value],
    })
    saving.value = false
    if (!updated) {
      error.value = store.error
      return
    }
    toast.success(t('account.userUpdated'))
  } else {
    const created = await store.createUser({
      email: email.value.trim(),
      username: username.value.trim(),
      password: password.value,
      fullName: fullName.value.trim(),
      appRole: appRole.value,
      roleNames: [...roleNames.value],
    })
    saving.value = false
    if (!created) {
      error.value = store.error
      return
    }
    toast.success(t('account.userCreated'))
  }

  open.value = false
  emit('saved')
}
</script>

<template>
  <Dialog
    v-model:open="open"
    :title="isCreate ? t('account.addUser') : t('account.editUser')"
    :icon="isCreate ? 'lucide-user-plus' : 'lucide-user-pen'"
    :actions="actions"
  >
    <div class="space-y-4">
      <ErrorMessage v-if="error" :message="error" />

      <TextInput
        v-if="isCreate"
        v-model="email"
        :label="t('field.email')"
        type="email"
        placeholder="abdulah@example.com"
        required
        autocomplete="off"
      />

      <TextInput
        v-if="isCreate"
        v-model="username"
        :label="t('field.username')"
        placeholder="abdulah"
        required
        autocomplete="off"
      />

      <Password
        v-if="isCreate"
        v-model="password"
        :label="t('field.password')"
        placeholder="••••••••"
        required
        autocomplete="new-password"
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

      <TextInput
        v-model="fullName"
        :label="t('account.fullName')"
        placeholder="Abdullah"
        required
      />

      <Select
        v-model="appRole"
        :label="t('account.appRole')"
        :options="appRoleOptions"
      />

      <MultiSelect
        v-model="roleNames"
        :label="t('account.roleNames')"
        :options="roleOptions"
        :placeholder="t('account.rolesPlaceholder')"
      />

      <Switch
        v-if="!isCreate"
        v-model="isActive"
        :label="t('account.isActive')"
      />
    </div>
  </Dialog>
</template>
