// Simple color helper for project
// Exports `getPaletteColorByNumber(color, number)` used by WaveBg
function clamp(v: number) {
  return Math.max(0, Math.min(255, Math.round(v)))
}

function hexToRgb(hex: string) {
  const h = hex.replace('#', '')
  const bigint = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16)
  return {
    r: (bigint >> 16) & 255,
    g: (bigint >> 8) & 255,
    b: bigint & 255
  }
}

function rgbToHex(r: number, g: number, b: number) {
  return (
    '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')
  )
}

// lightness: positive to lighten, negative to darken (fraction)
function adjustColor(hex: string, lightness: number) {
  try {
    const { r, g, b } = hexToRgb(hex)
    const nr = clamp(r + (255 - r) * lightness)
    const ng = clamp(g + (255 - g) * lightness)
    const nb = clamp(b + (255 - b) * lightness)
    return rgbToHex(nr, ng, nb)
  } catch (e) {
    return hex
  }
}

export function getPaletteColorByNumber(color: string, num: number) {
  // Provide a lightweight palette mapping for common numbers like 200/500
  // 200 -> lighter, 500 -> original, 700 -> darker
  const map: Record<number, number> = {
    50: 0.5,
    100: 0.35,
    200: 0.25,
    300: 0.12,
    400: 0.06,
    500: 0,
    600: -0.06,
    700: -0.12,
    800: -0.2,
    900: -0.35
  }

  const lightness = map[num] ?? 0
  // If color is a CSS variable like 'var(--color-primary)', return as-is for now
  if (typeof color === 'string' && color.trim().startsWith('var(')) return color

  // ensure color string
  try {
    return adjustColor(color, lightness)
  } catch (e) {
    return color
  }
}

export default { getPaletteColorByNumber }
