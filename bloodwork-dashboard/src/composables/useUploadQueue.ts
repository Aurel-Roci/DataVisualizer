import { computed, ref } from 'vue'
import * as api from '../api/bloodwork'
import { useBloodworkStore } from '../stores/bloodwork'
import { runPool } from '../utils/pool'

export type UploadStatus = 'pending' | 'uploading' | 'done' | 'failed'

export interface UploadItem {
  file: File
  status: UploadStatus
  error: string | null
}

// Uploads many PDFs with a few requests in flight at once, tracking each file's status.
// Results are refetched once at the end, not after every file.
export function useUploadQueue(concurrency = 3) {
  const store = useBloodworkStore()

  const items = ref<UploadItem[]>([])
  const running = ref(false)

  const count = (status: UploadStatus) => items.value.filter((i) => i.status === status).length
  const doneCount = computed(() => count('done'))
  const failedCount = computed(() => count('failed'))
  const finished = computed(() => doneCount.value + failedCount.value)

  function setFiles(files: File[]) {
    items.value = files.map((file) => ({ file, status: 'pending', error: null }))
  }

  // Uploads every pending or failed file, so calling it again retries the failures.
  async function start(metadata: api.UploadMetadata) {
    if (running.value) return
    running.value = true

    const todo = items.value.filter((i) => i.status === 'pending' || i.status === 'failed')
    try {
      await runPool(todo, concurrency, async (item) => {
        item.status = 'uploading'
        item.error = null
        try {
          await api.uploadBloodwork(item.file, metadata)
          item.status = 'done'
        } catch (e) {
          item.status = 'failed'
          item.error = api.describeError(e)
        }
      })
      if (doneCount.value > 0) await store.refresh()
    } finally {
      running.value = false
    }
  }

  return { items, running, doneCount, failedCount, finished, setFiles, start }
}
