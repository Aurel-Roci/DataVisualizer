<script setup lang="ts">
import { computed, ref } from 'vue'
import { useUploadQueue } from '../composables/useUploadQueue'

const emit = defineEmits<{ (e: 'close'): void }>()
const queue = useUploadQueue()

const name = ref('')
const birthday = ref('') // <input type="date"> gives YYYY-MM-DD

const completed = ref(false)

const STATUS_LABEL = { pending: '·', uploading: '…', done: '✓', failed: '✕' } as const

const hasFailures = computed(() => !queue.running.value && queue.failedCount.value > 0)
const pendingCount = computed(() => queue.items.value.length - queue.doneCount.value)

const submitLabel = computed(() => {
  if (queue.running.value) return `Uploading ${queue.finished.value} / ${queue.items.value.length}…`
  if (hasFailures.value) return `Retry failed (${queue.failedCount.value})`
  return pendingCount.value > 1 ? `Upload ${pendingCount.value} files` : 'Upload'
})

function onFiles(event: Event) {
  const files = (event.target as HTMLInputElement).files
  completed.value = false
  queue.setFiles(files ? Array.from(files) : [])
}

// backend expects DD/MM/YYYY
function toBackendDate(iso: string) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

function close() {
  if (!queue.running.value) emit('close')
}

async function submit() {
  await queue.start({
    name: name.value,
    birthday: birthday.value ? toBackendDate(birthday.value) : undefined,
  })
  // stay open on success; the user dismisses with "Done"
  completed.value = queue.items.value.length > 0 && queue.failedCount.value === 0
}
</script>

<template>
  <div class="backdrop" @click.self="close" @keydown.esc="close">
    <form
      class="dialog"
      role="dialog"
      aria-modal="true"
      aria-label="Upload bloodwork"
      @submit.prevent="submit"
    >
      <h2>Upload bloodwork PDFs</h2>

      <label class="field">
        <span>PDF files</span>
        <input
          type="file"
          accept="application/pdf,.pdf"
          multiple
          required
          :disabled="queue.running.value"
          @change="onFiles"
        />
      </label>

      <ul v-if="queue.items.value.length > 1 || hasFailures || completed" class="file-list">
        <li v-for="(item, i) in queue.items.value" :key="i" :class="item.status">
          <span class="file-status">{{ STATUS_LABEL[item.status] }}</span>
          <span class="file-name">{{ item.file.name }}</span>
          <span v-if="item.error" class="file-error">{{ item.error }}</span>
        </li>
      </ul>

      <label class="field">
        <span>Patient name (optional, applies to all files)</span>
        <input v-model="name" type="text" :disabled="queue.running.value" />
      </label>
      <label class="field">
        <span>Birthday (optional)</span>
        <input v-model="birthday" type="date" :disabled="queue.running.value" />
      </label>

      <div class="actions">
        <button
          v-if="!completed"
          type="button"
          class="btn-secondary"
          :disabled="queue.running.value"
          @click="close"
        >
          {{ hasFailures ? 'Close' : 'Cancel' }}
        </button>
        <button v-if="completed" type="button" class="btn-primary" @click="close">Done</button>
        <button
          v-else
          type="submit"
          class="btn-primary"
          :disabled="queue.items.value.length === 0 || queue.running.value || pendingCount === 0"
        >
          {{ submitLabel }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped src="./UploadDialog.css"></style>
