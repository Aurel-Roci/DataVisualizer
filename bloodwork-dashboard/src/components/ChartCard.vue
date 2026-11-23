<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import type { ChartOptions, Plugin } from 'chart.js'
import type { Marker } from '../types/bloodwork'
import { parseRange, statusFor, worstStatus } from '../utils/range'

const props = defineProps<{
  title: string
  series: Marker[]
}>()

const PALETTE = ['#006d77', '#d4831a', '#6b5ea8', '#2d7a4f']
const STATUS_COLOR = { ok: '#2d7a4f', warning: '#d4831a', danger: '#c0392b', none: '#8a95a3' }

const isSingle = computed(() => props.series.length === 1)

const latest = (m: Marker) => m.data[m.data.length - 1]

const status = computed(() =>
  worstStatus(
    props.series.map((m) => {
      const last = latest(m)
      return last ? statusFor(last.value, parseRange(m.reference_range)) : 'none'
    }),
  ),
)

const latestDate = computed(() => {
  const times = props.series.map((m) => latest(m)?.time ?? '').filter(Boolean)
  if (times.length === 0) return ''
  return formatMonth(times.reduce((a, b) => (a > b ? a : b)))
})

function formatMonth(time: string) {
  return new Date(time).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
}

// a lone series turns red/amber when out of range; grouped series keep their palette colour
const colors = computed(() =>
  props.series.map((_, i) =>
    isSingle.value && (status.value === 'danger' || status.value === 'warning')
      ? STATUS_COLOR[status.value]
      : PALETTE[i % PALETTE.length]!,
  ),
)

const legend = computed(() =>
  props.series.map((m, i) => ({
    name: m.test_name,
    color: colors.value[i]!,
    value: latest(m)?.value ?? null,
    unit: m.unit,
  })),
)

const chartData = computed(() => {
  const times = [...new Set(props.series.flatMap((m) => m.data.map((d) => d.time)))].sort()
  return {
    labels: times.map(formatMonth),
    datasets: props.series.map((m, i) => {
      const byTime = new Map(m.data.map((d) => [d.time, d.value]))
      const color = colors.value[i]!
      return {
        label: m.test_name,
        data: times.map((t) => byTime.get(t) ?? null),
        borderColor: color,
        backgroundColor: isSingle.value ? `${color}0d` : 'transparent',
        borderWidth: 2,
        pointRadius: 3.5,
        pointBackgroundColor: color,
        pointBorderColor: '#fff',
        pointBorderWidth: 1.5,
        tension: 0.3,
        fill: isSingle.value,
        spanGaps: true,
      }
    }),
  }
})

// shaded "normal" band, only meaningful when the chart has a single series
const refBandPlugins = computed<Plugin<'line'>[]>(() => {
  const range = isSingle.value ? parseRange(props.series[0]?.reference_range) : null
  if (!range) return []
  return [
    {
      id: 'refBand',
      beforeDatasetsDraw(chart) {
        const { ctx, chartArea, scales } = chart
        const y = scales.y
        if (!y) return
        const clamp = (px: number) => Math.min(Math.max(px, chartArea.top), chartArea.bottom)
        const top = range.high !== null ? clamp(y.getPixelForValue(range.high)) : chartArea.top
        const bottom = range.low !== null ? clamp(y.getPixelForValue(range.low)) : chartArea.bottom
        if (bottom <= top) return
        ctx.save()
        ctx.fillStyle = 'rgba(45, 122, 79, 0.08)'
        ctx.fillRect(chartArea.left, top, chartArea.right - chartArea.left, bottom - top)
        ctx.restore()
      },
    },
  ]
})

const chartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#0f1923',
      titleFont: { size: 11 },
      bodyFont: { size: 12 },
      padding: 8,
      cornerRadius: 6,
      callbacks: {
        label: (ctx) => {
          const unit = props.series[ctx.datasetIndex]?.unit ?? ''
          return `${ctx.dataset.label}: ${ctx.formattedValue} ${unit}`.trim()
        },
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { font: { size: 9, family: 'DM Mono' }, color: '#8a95a3' },
    },
    y: {
      grid: { color: '#eef1f5' },
      ticks: { font: { size: 9, family: 'DM Mono' }, color: '#8a95a3' },
    },
  },
}))
</script>

<template>
  <div class="chart-card">
    <div class="card-header">
      <div class="status-dot" :class="status" />
      <div class="card-title">{{ title }}</div>
      <div class="card-latest">latest · {{ latestDate }}</div>
    </div>

    <div class="card-legend">
      <div v-for="item in legend" :key="item.name" class="legend-item">
        <div class="legend-line" :style="{ background: item.color }" />
        {{ item.name }}
        <span class="legend-value">{{ item.value }} {{ item.unit }}</span>
      </div>
    </div>

    <div class="chart-body" :class="{ single: isSingle }">
      <Line :data="chartData" :options="chartOptions" :plugins="refBandPlugins" />
    </div>
  </div>
</template>

<style scoped src="./ChartCard.css"></style>
