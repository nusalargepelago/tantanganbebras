<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { CSSProperties } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

type Particle = { id: number; style: CSSProperties }
type Burst = { id: number; style: CSSProperties; pieceStyle: CSSProperties }
type SparkStyle = CSSProperties & { '--dx': string; '--dy': string; '--angle': string }
type Firework = {
  id: number
  style: CSSProperties
  flashStyle: CSSProperties
  sparks: { id: number; style: SparkStyle }[]
}

const COLORS = [
  'var(--surface-red-6)',
  'var(--surface-blue-6)',
  'var(--surface-green-6)',
  'var(--surface-amber-6)',
  'var(--surface-violet-6)',
  'var(--surface-pink-6)',
  'var(--surface-teal-6)',
  'var(--surface-orange-6)',
  'var(--surface-purple-6)',
  'var(--surface-cyan-6)',
]

const BALLOON_COUNT = 10
const RAIN_COUNT = 26
const BURST_MIN = 10
const BURST_MAX = 14
const FIREWORK_COUNT = 6
const SPARK_MIN = 22
const SPARK_MAX = 30
const NORMAL_END = 5200
const REDUCE_END = 2700

const reduce =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

const show = ref(false)
const balloons = ref<Particle[]>([])
const bursts = ref<Burst[]>([])
const drops = ref<Particle[]>([])
const fireworks = ref<Firework[]>([])

let seq = 0
let timers: ReturnType<typeof setTimeout>[] = []

let audioCtx: AudioContext | null = null
let noiseBuffer: AudioBuffer | null = null
let audioEnabled = true

function getAudio(): AudioContext | null {
  if (!audioEnabled) return null
  const Ctor =
    window.AudioContext ??
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!Ctor) return null
  if (!audioCtx) {
    try {
      audioCtx = new Ctor()
    } catch {
      return null
    }
  }
  if (audioCtx.state === 'suspended') void audioCtx.resume().catch(() => {})
  return audioCtx.state === 'running' ? audioCtx : null
}

function getNoise(ctx: AudioContext): AudioBuffer {
  if (noiseBuffer) return noiseBuffer
  const length = Math.floor(ctx.sampleRate * 0.25)
  noiseBuffer = ctx.createBuffer(1, length, ctx.sampleRate)
  const data = noiseBuffer.getChannelData(0)
  for (let i = 0; i < length; i++) data[i] = Math.random() * 2 - 1
  return noiseBuffer
}

function playPop(): void {
  const ctx = getAudio()
  if (!ctx) return
  const now = ctx.currentTime

  const noise = ctx.createBufferSource()
  noise.buffer = getNoise(ctx)
  const band = ctx.createBiquadFilter()
  band.type = 'bandpass'
  band.frequency.setValueAtTime(rand(900, 1600), now)
  band.Q.value = 1.1
  const noiseGain = ctx.createGain()
  noiseGain.gain.setValueAtTime(0.32, now)
  noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.07)
  noise.connect(band)
  band.connect(noiseGain)
  noiseGain.connect(ctx.destination)
  noise.start(now, rand(0, 0.15))
  noise.stop(now + 0.08)

  const thump = ctx.createOscillator()
  thump.type = 'sine'
  thump.frequency.setValueAtTime(rand(180, 240), now)
  thump.frequency.exponentialRampToValueAtTime(60, now + 0.09)
  const thumpGain = ctx.createGain()
  thumpGain.gain.setValueAtTime(0.18, now)
  thumpGain.gain.exponentialRampToValueAtTime(0.001, now + 0.1)
  thump.connect(thumpGain)
  thumpGain.connect(ctx.destination)
  thump.start(now)
  thump.stop(now + 0.11)
}

function playBoom(): void {
  const ctx = getAudio()
  if (!ctx) return
  const now = ctx.currentTime

  const noise = ctx.createBufferSource()
  noise.buffer = getNoise(ctx)
  const lowpass = ctx.createBiquadFilter()
  lowpass.type = 'lowpass'
  lowpass.frequency.setValueAtTime(520, now)
  lowpass.frequency.exponentialRampToValueAtTime(120, now + 0.35)
  const noiseGain = ctx.createGain()
  noiseGain.gain.setValueAtTime(0.14, now)
  noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.4)
  noise.connect(lowpass)
  lowpass.connect(noiseGain)
  noiseGain.connect(ctx.destination)
  noise.start(now, rand(0, 0.1))
  noise.stop(now + 0.42)

  const low = ctx.createOscillator()
  low.type = 'sine'
  low.frequency.setValueAtTime(95, now)
  low.frequency.exponentialRampToValueAtTime(42, now + 0.28)
  const lowGain = ctx.createGain()
  lowGain.gain.setValueAtTime(0.1, now)
  lowGain.gain.exponentialRampToValueAtTime(0.001, now + 0.3)
  low.connect(lowGain)
  lowGain.connect(ctx.destination)
  low.start(now)
  low.stop(now + 0.32)
}

function stopAudio(): void {
  audioEnabled = false
  if (!audioCtx) return
  const ctx = audioCtx
  audioCtx = null
  noiseBuffer = null
  void ctx.close().catch(() => {})
}

function rand(min: number, max: number): number {
  return min + Math.random() * (max - min)
}

function randInt(min: number, max: number): number {
  return Math.floor(rand(min, max + 1))
}

function pick<T>(arr: readonly T[]): T {
  return arr[randInt(0, arr.length - 1)]
}

function later(ms: number, fn: () => void): void {
  timers.push(setTimeout(fn, ms))
}

function spawnRain(): void {
  drops.value = Array.from({ length: RAIN_COUNT }, () => ({
    id: seq++,
    style: {
      left: `${rand(0, 100)}%`,
      top: '0',
      width: `${randInt(6, 11)}px`,
      height: `${randInt(6, 11)}px`,
      backgroundColor: pick(COLORS),
      borderRadius: Math.random() < 0.4 ? '9999px' : '1px',
      animationName: Math.random() < 0.5 ? 'celebration-rain-a' : 'celebration-rain-b',
      animationDuration: `${randInt(2600, 3800)}ms`,
      animationDelay: `${randInt(0, 1600)}ms`,
      animationTimingFunction: 'linear',
      animationFillMode: 'both',
    },
  }))
}

function spawnBurst(x: number, y: number): void {
  const count = randInt(BURST_MIN, BURST_MAX)
  for (let i = 0; i < count; i++) {
    bursts.value.push({
      id: seq++,
      style: {
        left: `${x}px`,
        top: `${y}px`,
        transform: `rotate(${rand(0, 360).toFixed(1)}deg) scale(${rand(0.6, 1.6).toFixed(2)})`,
      },
      pieceStyle: {
        width: `${randInt(6, 9)}px`,
        height: `${randInt(6, 9)}px`,
        backgroundColor: pick(COLORS),
        borderRadius: Math.random() < 0.4 ? '9999px' : '1px',
        animationName:
          Math.random() < 0.5 ? 'celebration-burst-a' : 'celebration-burst-b',
        animationDuration: `${randInt(650, 1000)}ms`,
        animationDelay: `${randInt(0, 120)}ms`,
        animationTimingFunction: 'cubic-bezier(0.2, 0.7, 0.4, 1)',
        animationFillMode: 'both',
      },
    })
  }
}

function spawnFirework(): void {
  const color = pick(COLORS)
  const count = randInt(SPARK_MIN, SPARK_MAX)
  const sparks = Array.from({ length: count }, (_, i) => {
    const angle = (i / count) * Math.PI * 2 + rand(-0.18, 0.18)
    const distance = rand(80, 160)
    const sparkColor = Math.random() < 0.35 ? 'var(--surface-amber-4)' : color
    return {
      id: seq++,
      style: {
        '--dx': `${(Math.cos(angle) * distance).toFixed(1)}px`,
        '--dy': `${(Math.sin(angle) * distance).toFixed(1)}px`,
        '--angle': `${((angle * 180) / Math.PI).toFixed(1)}deg`,
        width: '4px',
        height: `${randInt(12, 18)}px`,
        borderRadius: '9999px',
        backgroundColor: sparkColor,
        backgroundImage: `linear-gradient(to bottom, #ffffff, ${sparkColor} 65%)`,
        boxShadow: `0 0 12px ${sparkColor}`,
        animationName: 'celebration-firework-spark',
        animationDuration: `${randInt(800, 1200)}ms`,
        animationDelay: `${randInt(0, 140)}ms`,
        animationTimingFunction: 'cubic-bezier(0.15, 0.65, 0.3, 1)',
        animationFillMode: 'both',
      } as SparkStyle,
    }
  })
  fireworks.value.push({
    id: seq++,
    style: { left: `${rand(12, 88).toFixed(2)}%`, top: `${rand(10, 42).toFixed(2)}%` },
    flashStyle: { backgroundColor: color, boxShadow: `0 0 36px 12px ${color}` },
    sparks,
  })
  playBoom()
}

function spawnFireworks(): void {
  for (let i = 0; i < FIREWORK_COUNT; i++) {
    later(900 + i * 560 + randInt(0, 220), spawnFirework)
  }
}

function spawnBalloons(): void {
  const defs = Array.from({ length: BALLOON_COUNT }, () => {
    const width = randInt(26, 34)
    const height = randInt(32, 42)
    const delay = randInt(0, 900)
    const duration = randInt(1900, 2800)
    const left = rand(4, 90)
    const top = rand(12, 32)
    const id = seq++
    balloons.value.push({
      id,
      style: {
        left: `${left.toFixed(2)}%`,
        top: `${top.toFixed(2)}%`,
        width: `${width}px`,
        height: `${height}px`,
        backgroundColor: pick(COLORS),
        animationName: 'celebration-rise',
        animationDuration: `${duration}ms`,
        animationDelay: `${delay}ms`,
        animationTimingFunction: 'linear',
        animationFillMode: 'both',
      },
    })
    return { id, popAt: delay + duration, left, top, width, height }
  })

  for (const def of defs) {
    later(def.popAt, () => {
      const x = (def.left / 100) * window.innerWidth + def.width / 2
      const y = (def.top / 100) * window.innerHeight + def.height / 2
      spawnBurst(x, y)
      playPop()
      balloons.value = balloons.value.filter((b) => b.id !== def.id)
    })
  }
}

onMounted(() => {
  show.value = true
  if (!reduce) {
    spawnRain()
    spawnBalloons()
    spawnFireworks()
  }
  later(reduce ? REDUCE_END : NORMAL_END, () => {
    show.value = false
    balloons.value = []
    bursts.value = []
    drops.value = []
    fireworks.value = []
    stopAudio()
  })
})

onBeforeUnmount(() => {
  timers.forEach((timer) => clearTimeout(timer))
  timers = []
  stopAudio()
})
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="celebration-root" :class="{ 'is-reduce': reduce }">
      <div class="celebration-layer" aria-hidden="true">
        <span
          v-for="d in drops"
          :key="`rain-${d.id}`"
          class="celebration-rain"
          :style="d.style"
        />
      </div>
      <div class="celebration-layer" aria-hidden="true">
        <span
          v-for="b in balloons"
          :key="`balloon-${b.id}`"
          class="celebration-balloon"
          :style="b.style"
        />
        <span
          v-for="c in bursts"
          :key="`burst-${c.id}`"
          class="celebration-burst"
          :style="c.style"
        >
          <span class="celebration-piece" :style="c.pieceStyle" />
        </span>
      </div>
      <div class="celebration-layer" aria-hidden="true">
        <span
          v-for="f in fireworks"
          :key="`firework-${f.id}`"
          class="celebration-firework"
          :style="f.style"
        >
          <span class="celebration-flash" :style="f.flashStyle" />
          <span
            v-for="s in f.sparks"
            :key="`spark-${s.id}`"
            class="celebration-spark"
            :style="s.style"
          />
        </span>
      </div>
      <div class="celebration-layer celebration-center">
        <span class="celebration-title text-4xl-semibold text-ink-gray-8 sm:text-12xl-semibold">
          {{ t('celebration.title') }}
        </span>
      </div>
    </div>
  </Teleport>
</template>

<style>
.celebration-root {
  position: fixed;
  inset: 0;
  z-index: 60;
  pointer-events: none;
  overflow: hidden;
  animation: celebration-root-out 500ms 4600ms ease forwards;
}
.celebration-root.is-reduce {
  animation-delay: 2100ms;
}
.celebration-layer {
  position: absolute;
  inset: 0;
}
.celebration-center {
  display: flex;
  align-items: center;
  justify-content: center;
}
.celebration-title {
  padding: 0 1.25rem;
  max-width: 92vw;
  text-align: center;
  text-wrap: balance;
  animation: celebration-title 4800ms 350ms ease forwards;
}
.celebration-root.is-reduce .celebration-title {
  animation: celebration-title 2400ms 200ms ease forwards;
}
.celebration-balloon {
  position: absolute;
  border-radius: 50%;
  box-shadow: inset -6px -8px 12px rgba(0, 0, 0, 0.14);
}
.celebration-balloon::before {
  content: '';
  position: absolute;
  left: 18%;
  top: 14%;
  width: 26%;
  height: 20%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.55);
}
.celebration-balloon::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 100%;
  width: 1px;
  height: 16px;
  background: var(--ink-gray-4);
}
.celebration-rain {
  position: absolute;
  top: 0;
}
.celebration-burst {
  position: absolute;
}
.celebration-piece {
  display: block;
}
.celebration-firework {
  position: absolute;
}
.celebration-flash {
  position: absolute;
  left: -7px;
  top: -7px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  animation: celebration-flash 360ms ease-out both;
}
.celebration-spark {
  position: absolute;
  left: 0;
  top: 0;
}

@keyframes celebration-rise {
  0% {
    transform: translateY(118vh) translateX(0) rotate(-7deg);
    opacity: 0;
  }
  6% {
    opacity: 1;
  }
  35% {
    transform: translateY(74vh) translateX(-16px) rotate(6deg);
  }
  70% {
    transform: translateY(38vh) translateX(16px) rotate(-5deg);
  }
  100% {
    transform: translateY(0) translateX(-8px) rotate(4deg);
    opacity: 1;
  }
}

@keyframes celebration-title {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  14% {
    opacity: 1;
    transform: scale(1.1);
  }
  20% {
    transform: scale(1);
  }
  84% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(1.04);
  }
}

@keyframes celebration-root-out {
  to {
    opacity: 0;
  }
}

@keyframes celebration-rain-a {
  0% {
    transform: translateY(-6vh) rotate(0deg);
    opacity: 0;
  }
  8% {
    opacity: 0.95;
  }
  100% {
    transform: translateY(106vh) rotate(680deg);
    opacity: 0.95;
  }
}

@keyframes celebration-rain-b {
  0% {
    transform: translateY(-6vh) rotate(0deg);
    opacity: 0;
  }
  8% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(106vh) rotate(-540deg);
    opacity: 0.8;
  }
}

@keyframes celebration-burst-a {
  0% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 1;
  }
  70% {
    opacity: 1;
  }
  100% {
    transform: translate(88px, 170px) rotate(220deg);
    opacity: 0;
  }
}

@keyframes celebration-burst-b {
  0% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 1;
  }
  70% {
    opacity: 1;
  }
  100% {
    transform: translate(130px, 210px) rotate(-260deg);
    opacity: 0;
  }
}

@keyframes celebration-flash {
  0% {
    transform: scale(0.2);
    opacity: 0;
  }
  30% {
    transform: scale(1.5);
    opacity: 1;
  }
  100% {
    transform: scale(2.6);
    opacity: 0;
  }
}

@keyframes celebration-firework-spark {
  0% {
    transform: translate(0, 0) rotate(var(--angle)) scale(1);
    opacity: 1;
  }
  55% {
    opacity: 1;
  }
  100% {
    transform: translate(var(--dx), calc(var(--dy) + 42px)) rotate(var(--angle)) scale(0.3);
    opacity: 0;
  }
}
</style>
