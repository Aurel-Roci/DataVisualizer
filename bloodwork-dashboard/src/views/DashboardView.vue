<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import TopBar from '../components/TopBar.vue'
import ChartCard from '../components/ChartCard.vue'
import UploadDialog from '../components/UploadDialog.vue'
import RightSidebar from '../components/RightSidebar.vue'
import { useBloodworkStore } from '../stores/bloodwork'

const store = useBloodworkStore()
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
      <p v-if="store.loading" class="state">Loading…</p>
      <p v-else-if="store.error" class="state error">Error: {{ store.error }}</p>
      <p v-else-if="store.markers.length === 0" class="state">No results in this date range.</p>
      <p v-else-if="store.panels.length === 0" class="state">
        No markers selected. Pick some in the sidebar and press Apply Layout.
      </p>
      <ChartCard
        v-for="panel in store.panels"
        :key="panel.id"
        :title="panel.title"
        :series="panel.series"
      />
    </div>

    <RightSidebar />
    <UploadDialog v-if="uploadOpen" @close="uploadOpen = false" />
  </div>
</template>

<style scoped>
.dashboard {
  margin-right: var(--right-panel-w);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.content {
  padding: 24px 28px 48px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.state {
  font-size: 13px;
  color: var(--text-secondary);
}
.state.error {
  color: var(--danger);
}
</style>
