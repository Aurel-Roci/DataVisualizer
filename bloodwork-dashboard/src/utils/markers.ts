import type { BloodworkResult, Layout, Marker, MarkerGroup, Panel } from '../types/bloodwork'
import { groupFor, groupOrder } from './groups'

// Flat API rows -> one Marker per test, with its points sorted by time.
// Unit and reference range follow the most recent result.
export function buildMarkers(results: BloodworkResult[]): Marker[] {
  const byName = new Map<string, Marker>()

  for (const result of results) {
    let marker = byName.get(result.test_name)
    if (!marker) {
      marker = { test_name: result.test_name, unit: '', reference_range: '', data: [] }
      byName.set(result.test_name, marker)
    }
    marker.data.push({ time: result.time, value: result.value })
  }

  const latest = new Map<string, BloodworkResult>()
  for (const result of results) {
    const current = latest.get(result.test_name)
    if (!current || result.time >= current.time) latest.set(result.test_name, result)
  }

  for (const marker of byName.values()) {
    const last = latest.get(marker.test_name)!
    marker.unit = last.unit
    marker.reference_range = last.reference_range
    marker.data.sort((a, b) => a.time.localeCompare(b.time))
  }

  return [...byName.values()]
}

// Markers -> sidebar groups, in display order.
export function buildGroups(markers: Marker[]): MarkerGroup[] {
  const byGroup = new Map<string, Marker[]>()
  for (const marker of markers) {
    const name = groupFor(marker.test_name)
    byGroup.set(name, [...(byGroup.get(name) ?? []), marker])
  }

  return [...byGroup]
    .map(([name, list]) => ({
      name,
      markers: list.sort((a, b) => a.test_name.localeCompare(b.test_name)),
    }))
    .sort((a, b) => groupOrder(a.name) - groupOrder(b.name))
}

// Groups + the user's layout -> the chart cards to render.
export function buildPanels(groups: MarkerGroup[], layout: Layout): Panel[] {
  const selected = new Set(layout.selected)
  const panels: Panel[] = []

  for (const group of groups) {
    const active = group.markers.filter((m) => selected.has(m.test_name))
    if (active.length === 0) continue

    const combine = layout.groupInOne[group.name] && active.length > 1
    if (combine) {
      panels.push({ id: `group:${group.name}`, title: group.name, series: active })
    } else {
      for (const m of active) {
        panels.push({ id: `marker:${m.test_name}`, title: m.test_name, series: [m] })
      }
    }
  }
  return panels
}
