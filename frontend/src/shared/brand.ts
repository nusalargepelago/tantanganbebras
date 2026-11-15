import { computed, reactive, ref, watch } from 'vue'

interface Brand {
  name: string
  tagline: string
  description: string
  siteUrl: string
  logoUrl: string
}

declare global {
  interface Window {
    brand?: Brand
  }
}

const DEFAULT_BRAND: Brand = {
  name: 'Tantangan Bebras',
  tagline: '',
  description: '',
  siteUrl: '',
  logoUrl: '',
}

const injected = window.brand

export const brand = reactive<Brand>({
  name: injected?.name?.trim() || DEFAULT_BRAND.name,
  tagline: injected?.tagline ?? '',
  description: injected?.description ?? '',
  siteUrl: injected?.siteUrl ?? '',
  logoUrl: injected?.logoUrl ?? '',
})

export function setBrandLogo(url: string) {
  brand.logoUrl = url
  const icon = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
  if (icon) icon.href = url || 'data:,'
}

/**
 * Logo URL that falls back to empty when the image fails to load, so
 * components can render their default mark instead of a broken image.
 */
export function useBrandLogo() {
  const failed = ref(false)
  watch(
    () => brand.logoUrl,
    () => {
      failed.value = false
    },
  )
  const logoSrc = computed(() =>
    brand.logoUrl && !failed.value ? brand.logoUrl : '',
  )
  function onLogoError() {
    failed.value = true
  }
  return { logoSrc, onLogoError }
}
