import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { BloodworkResult, Marker, MarkerGroup } from '../types/bloodwork'
import * as api from '../api/bloodwork'
import { buildMarkers, buildGroups } from '../utils/markers'

// The data loaded from the backend for the current date range.
export const useBloodworkStore = defineStore('bloodwork', () => {
  const results = ref<BloodworkResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const startDate = ref('')
  const endDate = ref('')

  const markers = computed<Marker[]>(() => buildMarkers(results.value))
  const groups = computed<MarkerGroup[]>(() => buildGroups(markers.value))

  let inflight: AbortController | null = null

  async function fetchResults(start: string, end: string) {
    // a newer query supersedes any request still in flight
    inflight?.abort()
    const controller = new AbortController()
    inflight = controller

    startDate.value = start
    endDate.value = end
    loading.value = true
    error.value = null

    try {
      const data = await api.getResults(start, end, controller.signal)
      results.value = data.results
    } catch (e) {
      if (controller.signal.aborted) return // superseded; the newer call owns the state
      error.value = api.describeError(e)
    } finally {
      if (inflight === controller) {
        loading.value = false
        inflight = null
      }
    }
  }

  // re-run the last query
  function refresh() {
    return fetchResults(startDate.value, endDate.value)
  }

  return {
    results,
    loading,
    error,
    startDate,
    endDate,
    markers,
    groups,
    fetchResults,
    refresh,
  }
})
