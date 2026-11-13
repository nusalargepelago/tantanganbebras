<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Slider } from 'frappe-ui'

import { cropWindow, outputSize } from '@/shared/crop'

const props = withDefaults(defineProps<{ file: File; busy?: boolean }>(), {
  busy: false,
})
const emit = defineEmits<{
  cancel: []
  apply: [blob: Blob]
  error: []
}>()

const { t } = useI18n()

const MAX_SOURCE_EDGE = 2048
const MAX_ZOOM = 3

const stageEl = ref<HTMLElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)

const source = shallowRef<HTMLCanvasElement | HTMLImageElement | null>(null)
const srcW = ref(0)
const srcH = ref(0)
const status = ref<'loading' | 'ready' | 'loadFailed'>('loading')
const stage = ref(0)
const zoom = ref(1)
const center = reactive({ x: 0.5, y: 0.5 })
const dragging = ref(false)
const exporting = ref(false)

const sliderValue = computed(() => [zoom.value])
const canApply = computed(
  () => status.value === 'ready' && !props.busy && !exporting.value,
)

const dpr = Math.min(window.devicePixelRatio || 1, 2)

let objectUrl = ''
let loadToken = 0
let frame = 0
let observer: ResizeObserver | null = null
let pointerId: number | null = null
let dragStart = { x: 0, y: 0, cx: 0.5, cy: 0.5 }

function currentWindow() {
  return cropWindow(center.x, center.y, srcW.value, srcH.value, stage.value, zoom.value)
}

function scheduleDraw() {
  if (frame) return
  frame = requestAnimationFrame(() => {
    frame = 0
    draw()
  })
}

function draw() {
  const canvas = canvasEl.value
  const size = stage.value
  if (!canvas || !size) return

  const pixels = Math.round(size * dpr)
  if (canvas.width !== pixels || canvas.height !== pixels) {
    canvas.width = pixels
    canvas.height = pixels
  }
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, size, size)
  if (!source.value || status.value !== 'ready') return

  const win = currentWindow()
  if (!win.sw) return
  ctx.drawImage(source.value, win.sx, win.sy, win.sw, win.sh, 0, 0, size, size)
}

function measure() {
  const size = stageEl.value?.clientWidth ?? 0
  if (!size || size === stage.value) return
  stage.value = size
  scheduleDraw()
}

function release() {
  source.value = null
  srcW.value = 0
  srcH.value = 0
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = ''
  }
}

function buildSource(image: HTMLImageElement): {
  source: HTMLImageElement | HTMLCanvasElement
  width: number
  height: number
} {
  const width = image.naturalWidth
  const height = image.naturalHeight
  if (Math.max(width, height) <= MAX_SOURCE_EDGE) {
    return { source: image, width, height }
  }

  const scale = MAX_SOURCE_EDGE / Math.max(width, height)
  const cappedWidth = Math.max(1, Math.round(width * scale))
  const cappedHeight = Math.max(1, Math.round(height * scale))
  const canvas = document.createElement('canvas')
  canvas.width = cappedWidth
  canvas.height = cappedHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return { source: image, width, height }
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(image, 0, 0, cappedWidth, cappedHeight)
  return { source: canvas, width: cappedWidth, height: cappedHeight }
}

async function load(file: File) {
  const token = ++loadToken
  release()
  status.value = 'loading'
  zoom.value = 1
  center.x = 0.5
  center.y = 0.5

  objectUrl = URL.createObjectURL(file)
  const image = new Image()
  image.decoding = 'async'
  image.src = objectUrl
  try {
    await image.decode()
  } catch {
    if (token === loadToken) status.value = 'loadFailed'
    return
  }
  if (token !== loadToken) return
  if (!image.naturalWidth || !image.naturalHeight) {
    status.value = 'loadFailed'
    return
  }

  const prepared = buildSource(image)
  source.value = prepared.source
  srcW.value = prepared.width
  srcH.value = prepared.height
  status.value = 'ready'
  await nextTick()
  measure()
  scheduleDraw()
}

function onZoom(value: number[] | undefined) {
  const next = value?.[0]
  if (typeof next !== 'number' || !Number.isFinite(next)) return
  zoom.value = Math.min(MAX_ZOOM, Math.max(1, next))
  if (zoom.value <= 1) {
    zoom.value = 1
    center.x = 0.5
    center.y = 0.5
  }
  scheduleDraw()
}

function onPointerDown(event: PointerEvent) {
  if (status.value !== 'ready' || props.busy || event.button !== 0) return
  const el = stageEl.value
  if (!el) return

  el.setPointerCapture(event.pointerId)
  pointerId = event.pointerId
  dragging.value = true
  dragStart = { x: event.clientX, y: event.clientY, cx: center.x, cy: center.y }
}

function onPointerMove(event: PointerEvent) {
  if (!dragging.value || event.pointerId !== pointerId) return
  const win = currentWindow()
  if (!win.scale) return

  center.x = dragStart.cx - (event.clientX - dragStart.x) / (srcW.value * win.scale)
  center.y = dragStart.cy - (event.clientY - dragStart.y) / (srcH.value * win.scale)
  const clamped = currentWindow()
  center.x = clamped.cx
  center.y = clamped.cy
  scheduleDraw()
}

function endDrag(event: PointerEvent) {
  if (pointerId === null || event.pointerId !== pointerId) return
  const el = stageEl.value
  if (el?.hasPointerCapture(pointerId)) el.releasePointerCapture(pointerId)
  pointerId = null
  dragging.value = false
}

async function apply() {
  if (!canApply.value) return
  const src = source.value
  const win = currentWindow()
  if (!src || !win.sw) return

  exporting.value = true
  try {
    const out = outputSize(win.sw)
    const canvas = document.createElement('canvas')
    canvas.width = out
    canvas.height = out
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      emit('error')
      return
    }
    ctx.imageSmoothingQuality = 'high'
    ctx.drawImage(src, win.sx, win.sy, win.sw, win.sh, 0, 0, out, out)

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, 'image/png')
    })
    if (!blob) {
      emit('error')
      return
    }
    emit('apply', blob)
  } finally {
    exporting.value = false
  }
}

watch(
  () => props.file,
  (file) => {
    void load(file)
  },
  { immediate: true },
)

onMounted(() => {
  observer = new ResizeObserver(measure)
  if (stageEl.value) observer.observe(stageEl.value)
  measure()
})

onBeforeUnmount(() => {
  loadToken += 1
  release()
  observer?.disconnect()
  observer = null
  if (frame) cancelAnimationFrame(frame)
})
</script>

<template>
  <div class="mt-6">
    <div class="text-base-medium leading-tighter text-ink-gray-8">
      {{ t('settings.brand.crop.title') }}
    </div>

    <div
      ref="stageEl"
      role="img"
      :aria-label="t('settings.brand.crop.stage')"
      class="relative mx-auto mt-4 aspect-square w-full max-w-[280px] touch-none select-none overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-gray-2"
      :class="dragging ? 'cursor-grabbing' : 'cursor-grab'"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="endDrag"
      @pointercancel="endDrag"
      @lostpointercapture="endDrag"
    >
      <canvas ref="canvasEl" class="block h-full w-full" />
      <div
        v-if="status === 'loading'"
        class="absolute inset-0 grid place-items-center bg-surface-gray-2/90 text-ink-gray-5"
      >
        <span class="lucide-loader-circle size-5 animate-spin" aria-hidden="true" />
      </div>
      <div
        v-else-if="status === 'loadFailed'"
        class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-surface-gray-2 p-4 text-center text-p-sm text-ink-gray-5"
      >
        <span class="lucide-image-off size-5" aria-hidden="true" />
        {{ t('settings.brand.crop.loadFailed') }}
      </div>
    </div>

    <p class="mt-3 text-p-sm leading-5 text-ink-gray-5">
      {{ t('settings.brand.crop.hint') }}
    </p>

    <div class="mt-4 flex items-center gap-3">
      <span class="text-p-sm text-ink-gray-6">
        {{ t('settings.brand.crop.zoom') }}
      </span>
      <Slider
        class="flex-1"
        :model-value="sliderValue"
        :min="1"
        :max="MAX_ZOOM"
        :step="0.05"
        :disabled="status !== 'ready' || busy"
        :aria-label="t('settings.brand.crop.zoom')"
        @update:model-value="onZoom"
      />
      <span class="w-12 text-right text-p-sm tabular-nums text-ink-gray-6">
        {{ zoom.toFixed(2) }}×
      </span>
    </div>

    <div class="mt-4 flex flex-wrap gap-2">
      <Button
        variant="solid"
        theme="gray"
        icon-left="lucide-check"
        :label="t('settings.brand.crop.apply')"
        :loading="busy || exporting"
        :disabled="!canApply"
        @click="apply"
      />
      <Button
        variant="subtle"
        theme="gray"
        :label="t('settings.brand.crop.cancel')"
        :disabled="busy || exporting"
        @click="emit('cancel')"
      />
    </div>
  </div>
</template>
