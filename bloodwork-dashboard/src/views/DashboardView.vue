<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import TopBar from '../components/TopBar.vue'
import ChartCard from '../components/ChartCard.vue'
import UploadDialog from '../components/UploadDialog.vue'
import RightSidebar from '../components/RightSidebar.vue'
import { useBloodworkStore } from '../stores/bloodwork'
import { useLayoutStore } from '../stores/layout'

const store = useBloodworkStore()
const layout = useLayoutStore()
const uploadOpen = ref(false)

// local calendar date as YYYY-MM-DD (toISOString would shift to UTC)
function localDate(d: Date) {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// default window: the last two years
const today = new Date()
const twoYearsAgo = new Date(today)
twoYearsAgo.setFullYear(today.getFullYear() - 2)
const from = ref(localDate(twoYearsAgo))
const to = ref(localDate(today))

// refetch whenever a complete, valid range is picked (also runs on mount)
watch(
  [from, to],
  ([f, t]) => {
    if (f && t && f <= t) store.fetchResults(`${f}T00:00:00`, `${t}T23:59:59`)
  },
  { immediate: true },
)

const subtitle = computed(() => (store.startDate ? `${from.value} → ${to.value}` : 'loading…'))

// One line of status text above the charts, if there's anything to say.
const status = computed<{ text: string; isError: boolean } | null>(() => {
  const hasData = store.markers.length > 0

  if (store.error) return { text: `Error: ${store.error}`, isError: true }
  if (store.loading) return { text: hasData ? 'Refreshing…' : 'Loading…', isError: false }
  if (!hasData) return { text: 'No results in this date range.', isError: false }
  if (layout.panels.length === 0) {
    return {
      text: 'No markers selected. Pick some in the sidebar and press Apply Layout.',
      isError: false,
    }
  }
  return null
})
</script>

<template>
  <div class="dashboard">
    <TopBar
      title="Bloodwork Dashboard"
      v-model:from="from"
      v-model:to="to"
      :subtitle="subtitle"
      @add="uploadOpen = true"
    />

    <div class="content">
      <p v-if="status" class="state" :class="{ error: status.isError }">{{ status.text }}</p>
      <ChartCard
        v-for="panel in layout.panels"
        :key="panel.id"
        :title="panel.title"
        :series="panel.series"
      />
    </div>

    <RightSidebar />
    <UploadDialog v-if="uploadOpen" @close="uploadOpen = false" />
  </div>
</template>

<style scoped src="./DashboardView.css"></style>
