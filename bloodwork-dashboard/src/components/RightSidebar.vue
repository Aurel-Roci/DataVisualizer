<script setup lang="ts">
import { computed, ref } from 'vue'
import { useBloodworkStore } from '../stores/bloodwork'
import { useLayoutStore } from '../stores/layout'

const bloodwork = useBloodworkStore()
const layout = useLayoutStore()

// Groups are expanded by default; we only remember the ones the user collapsed,
// so groups that show up later (e.g. after changing the date range) start expanded too.
const collapsed = ref<Set<string>>(new Set())

const isOpen = (name: string) => !collapsed.value.has(name)

function toggleOpen(name: string) {
  const next = new Set(collapsed.value)
  if (!next.delete(name)) next.add(name)
  collapsed.value = next
}

const selected = computed(() => new Set(layout.draft.selected))
// selections can include markers outside the current date range, so count only visible ones
const activeCount = computed(
  () => bloodwork.markers.filter((m) => selected.value.has(m.test_name)).length,
)
const totalMarkers = computed(() => bloodwork.markers.length)

function selectedIn(group: { markers: { test_name: string }[] }) {
  return group.markers.filter((m) => selected.value.has(m.test_name)).length
}
</script>

<template>
  <aside class="right-sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">Markers</div>
      <div class="sidebar-meta">{{ activeCount }} of {{ totalMarkers }} markers active</div>
    </div>

    <div class="sidebar-body">
      <div
        v-for="group in bloodwork.groups"
        :key="group.name"
        class="group-block"
        :class="{ open: isOpen(group.name) }"
      >
        <button
          type="button"
          class="group-header"
          :aria-expanded="isOpen(group.name)"
          @click="toggleOpen(group.name)"
        >
          <span class="chevron">▶</span>
          <span class="group-name">{{ group.name }}</span>
          <span class="group-count">{{ selectedIn(group) }} / {{ group.markers.length }}</span>
        </button>

        <div v-if="isOpen(group.name)" class="group-body">
          <label class="group-option">
            <input
              type="checkbox"
              class="toggle"
              :checked="layout.draft.groupInOne[group.name] ?? false"
              @change="
                layout.setGroupInOne(group.name, ($event.target as HTMLInputElement).checked)
              "
            />
            Group in one chart
          </label>

          <label v-for="m in group.markers" :key="m.test_name" class="marker-row">
            <input
              type="checkbox"
              class="cb"
              :checked="selected.has(m.test_name)"
              @change="layout.toggleMarker(m.test_name)"
            />
            <span class="marker-name">{{ m.test_name }}</span>
            <span class="marker-unit">{{ m.unit }}</span>
          </label>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="sidebar-stat">
        <span>Panels shown</span><span>{{ layout.panels.length }}</span>
      </div>
      <div class="sidebar-stat"><span>Markers active</span><span>{{ activeCount }}</span></div>
      <button type="button" class="btn-primary btn-block" @click="layout.applyLayout()">
        Apply Layout
      </button>
    </div>
  </aside>
</template>

<style scoped src="./RightSidebar.css"></style>
