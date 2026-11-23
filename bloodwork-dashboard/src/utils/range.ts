export interface ParsedRange {
  low: number | null
  high: number | null
}

export type Status = 'ok' | 'warning' | 'danger' | 'none'

const NUM = String.raw`(\d+(?:\.\d+)?)`
const BETWEEN = new RegExp(`${NUM}\\s*(?:-|–|—|to)\\s*${NUM}`, 'i')
const UPPER = new RegExp(`(?:<=?|≤|up to|max\\.?)\\s*${NUM}`, 'i')
const LOWER = new RegExp(`(?:>=?|≥|min\\.?)\\s*${NUM}`, 'i')

// Reference ranges come from PDF text, e.g. "70 - 100 mg/dL", "< 200", "> 40 mg/dL".
export function parseRange(raw: string | null | undefined): ParsedRange | null {
  if (!raw) return null
  const text = raw.replace(/(\d),(\d)/g, '$1.$2') // decimal commas

  const upper = UPPER.exec(text)
  if (upper) return { low: null, high: parseFloat(upper[1]!) }

  const lower = LOWER.exec(text)
  if (lower) return { low: parseFloat(lower[1]!), high: null }

  const between = BETWEEN.exec(text)
  if (between) {
    const a = parseFloat(between[1]!)
    const b = parseFloat(between[2]!)
    return { low: Math.min(a, b), high: Math.max(a, b) }
  }
  return null
}

// in range → ok; within 15% of the bound → warning; further → danger
export function statusFor(value: number, range: ParsedRange | null): Status {
  if (!range) return 'none'
  const { low, high } = range

  let distance = 0
  let bound = 0
  if (high !== null && value > high) {
    distance = value - high
    bound = high
  } else if (low !== null && value < low) {
    distance = low - value
    bound = low
  } else {
    return 'ok'
  }

  const tolerance = Math.abs(bound) * 0.15
  return distance <= tolerance ? 'warning' : 'danger'
}

const SEVERITY: Record<Status, number> = { none: 0, ok: 1, warning: 2, danger: 3 }

export function worstStatus(statuses: Status[]): Status {
  return statuses.reduce<Status>((w, s) => (SEVERITY[s] > SEVERITY[w] ? s : w), 'none')
}
