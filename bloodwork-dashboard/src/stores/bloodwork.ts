import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  BloodworkResult,
  BloodworkResponse,
  Marker,
  MarkerGroup,
  Panel,
  Layout,
} from '../types/bloodwork'
import { API_BASE_URL } from '../config'
import { groupFor, groupOrder } from '../utils/groups'

export const useBloodworkStore = defineStore('bloodwork', () => {
  // --- state ---
  const results = ref<BloodworkResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const startDate = ref('')
  const endDate = ref('')

  // sidebar choices being edited (draft) vs. what the dashboard currently shows (applied)
  const draft = ref<Layout>({ selected: [], groupInOne: {} })
  const applied = ref<Layout>({ selected: [], groupInOne: {} })
  let layoutInitialized = false

  // --- getters ---
  const markers = computed<Marker[]>(() => {
    const grouped = new Map<string, Marker>()
    const latestTime = new Map<string, string>()

    for (const result of results.value) {
      let marker = grouped.get(result.test_name)
      if (!marker) {
        marker = {
          test_name: result.test_name,
          unit: result.unit,
          reference_range: result.reference_range,
          data: [],
        }
        grouped.set(result.test_name, marker)
      }
      marker.data.push({ time: result.time, value: result.value })

      // unit / reference range follow the most recent result
      if (result.time >= (latestTime.get(result.test_name) ?? '')) {
        latestTime.set(result.test_name, result.time)
        marker.unit = result.unit
        marker.reference_range = result.reference_range
      }
    }

    for (const marker of grouped.values()) {
      marker.data.sort((a, b) => a.time.localeCompare(b.time))
    }

    return Array.from(grouped.values())
  })

  const groups = computed<MarkerGroup[]>(() => {
    const byGroup = new Map<string, Marker[]>()
    for (const marker of markers.value) {
      const name = groupFor(marker.test_name)
      byGroup.set(name, [...(byGroup.get(name) ?? []), marker])
    }
    return Array.from(byGroup, ([name, list]) => ({
      name,
      markers: list.sort((a, b) => a.test_name.localeCompare(b.test_name)),
    })).sort((a, b) => groupOrder(a.name) - groupOrder(b.name))
  })

  const panels = computed<Panel[]>(() => {
    const selected = new Set(applied.value.selected)
    const out: Panel[] = []

    for (const group of groups.value) {
      const active = group.markers.filter((m) => selected.has(m.test_name))
      if (active.length === 0) continue

      if (applied.value.groupInOne[group.name] && active.length > 1) {
        out.push({ id: `group:${group.name}`, title: group.name, series: active })
      } else {
        for (const m of active) {
          out.push({ id: `marker:${m.test_name}`, title: m.test_name, series: [m] })
        }
      }
    }
    return out
  })

  // --- layout actions ---
  function toggleMarker(name: string) {
    const sel = draft.value.selected
    draft.value.selected = sel.includes(name) ? sel.filter((n) => n !== name) : [...sel, name]
  }

  function setGroupInOne(group: string, value: boolean) {
    draft.value.groupInOne = { ...draft.value.groupInOne, [group]: value }
  }

  function applyLayout() {
    applied.value = {
      selected: [...draft.value.selected],
      groupInOne: { ...draft.value.groupInOne },
    }
  }

  // first load: everything selected, groups combined into one chart
  function initLayout() {
    if (layoutInitialized || markers.value.length === 0) return
    layoutInitialized = true
    draft.value = {
      selected: markers.value.map((m) => m.test_name),
      groupInOne: Object.fromEntries(groups.value.map((g) => [g.name, true])),
    }
    applyLayout()
  }

  // --- data ---
  async function fetchResults(start: string, end: string) {
    startDate.value = start
    endDate.value = end
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({ start_date: start, end_date: end })
      const response = await fetch(`${API_BASE_URL}/results?${params}`)

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`)
      }

      const data: BloodworkResponse = await response.json()
      results.value = data.results
      initLayout()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  // re-run the last query (e.g. after an upload)
  function refresh() {
    return fetchResults(startDate.value, endDate.value)
  }

  // upload a PDF to the backend; throws an Error with the backend's message on failure
  async function uploadBloodwork(file: File, name?: string, birthday?: string) {
    const body = new FormData()
    body.append('file', file)
    if (name?.trim()) body.append('name', name.trim())
    if (birthday) body.append('birthday', birthday) // DD/MM/YYYY

    const response = await fetch(`${API_BASE_URL}/upload-bloodwork`, { method: 'POST', body })
    if (!response.ok) {
      let message = `Upload failed (${response.status})`
      try {
        const payload = await response.json()
        if (typeof payload.detail === 'string') message = payload.detail
      } catch {
        // non-JSON error body: keep the generic message
      }
      throw new Error(message)
    }
    await refresh()
  }

  return {
    results,
    loading,
    error,
    startDate,
    endDate,
    draft,
    markers,
    groups,
    panels,
    toggleMarker,
    setGroupInOne,
    applyLayout,
    fetchResults,
    refresh,
    uploadBloodwork,
  }
})
