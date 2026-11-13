export interface CropWindow {
  cx: number
  cy: number
  sx: number
  sy: number
  sw: number
  sh: number
  scale: number
}

export const MAX_OUTPUT_EDGE = 512

const NO_WINDOW: CropWindow = {
  cx: 0.5,
  cy: 0.5,
  sx: 0,
  sy: 0,
  sw: 0,
  sh: 0,
  scale: 0,
}

function clampCenter(value: number, share: number): number {
  if (!Number.isFinite(value)) return 0.5
  const low = share
  const high = 1 - share
  if (high < low) return 0.5
  return Math.min(Math.max(value, low), high)
}

/**
 * Square source window shown by a cover-fit stage of `stage` px.
 * `cx`/`cy` are normalized image coordinates at the stage centre.
 */
export function cropWindow(
  cx: number,
  cy: number,
  srcW: number,
  srcH: number,
  stage: number,
  zoom: number,
): CropWindow {
  if (!(srcW > 0) || !(srcH > 0) || !(stage > 0)) return { ...NO_WINDOW }

  const scale = Math.max(stage / srcW, stage / srcH) * Math.max(zoom, 1)
  const half = stage / (2 * scale)
  const sw = Math.min(2 * half, srcW, srcH)

  const x = clampCenter(cx, half / srcW)
  const y = clampCenter(cy, half / srcH)
  const sx = Math.min(Math.max(x * srcW - half, 0), srcW - sw)
  const sy = Math.min(Math.max(y * srcH - half, 0), srcH - sw)

  return { cx: x, cy: y, sx, sy, sw, sh: sw, scale }
}

export function outputSize(sw: number): number {
  if (!Number.isFinite(sw)) return 1
  return Math.min(MAX_OUTPUT_EDGE, Math.max(1, Math.round(sw)))
}
