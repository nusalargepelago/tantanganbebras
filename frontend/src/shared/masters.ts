import { api } from './api'

export interface MasterOption {
  label: string
  value: string
}

export interface SchoolItem {
  id: string
  name: string
  isActive: boolean
  cityId?: string
  city?: { id: string; name: string } | null
}

export interface CityItem {
  id: string
  name: string
}

let schoolCache: SchoolItem[] | null = null
let schoolCachePromise: Promise<SchoolItem[]> | null = null
let cityCache: CityItem[] | null = null
let cityCachePromise: Promise<CityItem[]> | null = null

export async function fetchSchools(): Promise<SchoolItem[]> {
  if (schoolCache) return schoolCache
  if (!schoolCachePromise) {
    schoolCachePromise = api
      .get<{ items: SchoolItem[] }>('/school')
      .then(({ data }) => {
        schoolCache = data.items ?? []
        return schoolCache
      })
      .finally(() => {
        schoolCachePromise = null
      })
  }
  return schoolCachePromise
}

export async function fetchCities(): Promise<CityItem[]> {
  if (cityCache) return cityCache
  if (!cityCachePromise) {
    cityCachePromise = api
      .get<{ items: CityItem[] }>('/city')
      .then(({ data }) => {
        cityCache = data.items ?? []
        return cityCache
      })
      .finally(() => {
        cityCachePromise = null
      })
  }
  return cityCachePromise
}

export function schoolOptions(schools: SchoolItem[]): MasterOption[] {
  return schools.map((s) => ({ label: s.name, value: s.id }))
}

export function cityOptions(cities: CityItem[]): MasterOption[] {
  return cities.map((c) => ({ label: c.name, value: c.id }))
}

export function invalidateMasters() {
  schoolCache = null
  cityCache = null
}
