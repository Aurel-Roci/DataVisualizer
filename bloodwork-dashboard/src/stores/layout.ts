import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import type { Layout, Panel } from '../types/bloodwork'
import { useBloodworkStore } from './bloodwork'
import { buildPanels } from '../utils/markers'

// Which markers the user wants charted, and how they're combined.
// `draft` is what the sidebar edits; `applied` is what the dashboard shows.
export const useLayoutStore = defineStore('layout', () => {
  const bloodwork = useBloodworkStore()

  const draft = ref<Layout>({ selected: [], groupInOne: {} })
  const applied = ref<Layout>({ selected: [], groupInOne: {} })

  const panels = computed<Panel[]>(() => buildPanels(bloodwork.groups, applied.value))

  function toggleMarker(name: string) {
    const selected = draft.value.selected
    draft.value.selected = selected.includes(name)
      ? selected.filter((n) => n !== name)
      : [...selected, name]
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

  // Markers and groups seen for the first time start selected, and groups start
  // combined into one chart. They're added to both layouts so unapplied sidebar
  // edits aren't applied by accident.
  const knownMarkers = new Set<string>()
  const knownGroups = new Set<string>()

  watch(
    () => bloodwork.groups,
    (groups) => {
      const newMarkers = groups
        .flatMap((g) => g.markers.map((m) => m.test_name))
        .filter((name) => !knownMarkers.has(name))
      const newGroups = groups.map((g) => g.name).filter((name) => !knownGroups.has(name))

      newMarkers.forEach((name) => knownMarkers.add(name))
      newGroups.forEach((name) => knownGroups.add(name))

      for (const layout of [draft, applied]) {
        layout.value = {
          selected: [...layout.value.selected, ...newMarkers],
          groupInOne: {
            ...Object.fromEntries(newGroups.map((name) => [name, true])),
            ...layout.value.groupInOne,
          },
        }
      }
    },
    { immediate: true },
  )

  return { draft, panels, toggleMarker, setGroupInOne, applyLayout }
})
