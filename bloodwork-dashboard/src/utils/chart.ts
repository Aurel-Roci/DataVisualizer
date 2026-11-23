import type { ChartData, ChartOptions, Plugin } from 'chart.js'
import type { DataPoint, Marker } from '../types/bloodwork'
import type { ParsedRange, Status } from './range'

const PALETTE = ['#006d77', '#d4831a', '#6b5ea8', '#2d7a4f']
const STATUS_COLOR: Record<Status, string> = {
  ok: '#2d7a4f',
  warning: '#d4831a',
  danger: '#c0392b',
  none: '#8a95a3',
}

// e.g. "Mar 14, 26". Day-level so two results in one month get distinct labels.
export function formatDay(time: string): string {
  return new Date(time).toLocaleDateString('en-US', {
    day: 'numeric',
    month: 'short',
    year: '2-digit',
  })
}

export function latestPoint(marker: Marker): DataPoint | undefined {
  return marker.data[marker.data.length - 1]
}

// Time of the newest data point across all series, or null if there is none.
export function latestTime(series: Marker[]): string | null {
  const times = series.flatMap((m) => latestPoint(m)?.time ?? [])
  return times.length > 0 ? times.reduce((a, b) => (a > b ? a : b)) : null
}

// A lone series turns amber/red when out of range; grouped series keep their palette colour.
export function seriesColors(series: Marker[], status: Status): string[] {
  const highlight = series.length === 1 && (status === 'warning' || status === 'danger')
  return series.map((_, i) => (highlight ? STATUS_COLOR[status] : PALETTE[i % PALETTE.length]!))
}

export function buildChartData(series: Marker[], colors: string[]): ChartData<'line'> {
  const single = series.length === 1
  const times = [...new Set(series.flatMap((m) => m.data.map((d) => d.time)))].sort()

  return {
    labels: times.map(formatDay),
    datasets: series.map((marker, i) => {
      const valueAt = new Map(marker.data.map((d) => [d.time, d.value]))
      const color = colors[i]!
      return {
        label: marker.test_name,
        data: times.map((t) => valueAt.get(t) ?? null),
        borderColor: color,
        backgroundColor: single ? `${color}0d` : 'transparent',
        borderWidth: 2,
        pointRadius: 3.5,
        pointBackgroundColor: color,
        pointBorderColor: '#fff',
        pointBorderWidth: 1.5,
        tension: 0.3,
        fill: single,
        spanGaps: true,
      }
    }),
  }
}

const TICK_STYLE = { font: { size: 9, family: 'DM Mono' }, color: '#8a95a3' }

export function buildChartOptions(series: Marker[]): ChartOptions<'line'> {
  return {
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
            const unit = series[ctx.datasetIndex]?.unit ?? ''
            return `${ctx.dataset.label}: ${ctx.formattedValue} ${unit}`.trim()
          },
        },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: TICK_STYLE },
      y: { grid: { color: '#eef1f5' }, ticks: TICK_STYLE },
    },
  }
}

// Shades the "normal" range behind the line. Open-ended ranges (e.g. "< 200")
// extend to the edge of the chart.
export function referenceBandPlugin(range: ParsedRange): Plugin<'line'> {
  return {
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
  }
}
