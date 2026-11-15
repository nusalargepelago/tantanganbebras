<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Combobox, Dialog, ErrorMessage, FormControl, toast, type DialogAction } from 'frappe-ui'

import { api, getErrorMessage } from '@/shared/api'
import { cityOptions, fetchCities, type SchoolItem } from '@/shared/masters'

const props = defineProps<{
  open: boolean
  initialName?: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  created: [school: SchoolItem]
}>()

const { t } = useI18n()
const form = reactive({ name: '', cityId: null as string | null })
const cities = ref<{ label: string; value: string }[]>([])
const saving = ref(false)
const citiesFailed = ref(false)

const canSave = computed(
  () => form.name.trim() !== '' && !!form.cityId && !saving.value && !citiesFailed.value,
)

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    form.name = props.initialName ?? ''
    form.cityId = null
    saving.value = false
    citiesFailed.value = false
    try {
      cities.value = cityOptions(await fetchCities())
    } catch {
      citiesFailed.value = true
    }
  },
)

async function onSave(close: () => void) {
  const name = form.name.trim()
  if (!canSave.value) return
  saving.value = true
  try {
    const { data } = await api.post<SchoolItem>('/school', { name, cityId: form.cityId })
    toast.success(t('schools.createdToast'))
    emit('created', data)
    close()
  } catch (e: any) {
    toast.error(getErrorMessage(e, t('schools.saveFailed')))
  } finally {
    saving.value = false
  }
}

function submit() {
  onSave(() => emit('update:open', false))
}

const actions = computed<DialogAction[]>(() => [
  {
    label: t('shared.cancel'),
    variant: 'outline',
    theme: 'gray',
    onClick: ({ close }: { close: () => void }) => close(),
  },
  {
    label: t('schools.add'),
    variant: 'solid',
    theme: 'gray',
    iconLeft: 'lucide-plus',
    loading: saving.value,
    disabled: !canSave.value,
    onClick: ({ close }: { close: () => void }) => onSave(close),
  },
])
</script>

<template>
  <Dialog
    :open="open"
    :title="t('schools.add')"
    size="sm"
    :actions="actions"
    @update:open="emit('update:open', $event)"
  >
    <div class="space-y-4">
      <ErrorMessage v-if="citiesFailed" :message="t('schools.citiesLoadFailed')" />
      <FormControl
        v-model="form.name"
        :label="t('schools.name')"
        :placeholder="t('schools.namePlaceholder')"
        required
        @keyup.enter="submit"
      />
      <Combobox
        v-model="form.cityId"
        :label="t('schools.city')"
        :options="cities"
        :placeholder="t('schools.cityPlaceholder')"
        :required="true"
      />
    </div>
  </Dialog>
</template>
