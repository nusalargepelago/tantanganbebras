export interface Brand {
  name: string
  tagline: string
  description: string
  siteUrl: string
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
}

const injected = window.brand

export const brand: Brand = {
  name: injected?.name?.trim() || DEFAULT_BRAND.name,
  tagline: injected?.tagline ?? '',
  description: injected?.description ?? '',
  siteUrl: injected?.siteUrl ?? '',
}
