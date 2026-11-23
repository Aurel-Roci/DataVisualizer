<script setup lang="ts">
import { ref } from 'vue'
import { useBloodworkStore } from '../stores/bloodwork'

const emit = defineEmits<{ (e: 'close'): void }>()
const store = useBloodworkStore()

const file = ref<File | null>(null)
const name = ref('')
const birthday = ref('') // <input type="date"> gives YYYY-MM-DD
const submitting = ref(false)
const error = ref<string | null>(null)

function onFile(event: Event) {
  file.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

// backend expects DD/MM/YYYY
function toBackendDate(iso: string) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

async function submit() {
  if (!file.value || submitting.value) return
  submitting.value = true
  error.value = null
  try {
    await store.uploadBloodwork(
      file.value,
      name.value,
      birthday.value ? toBackendDate(birthday.value) : undefined,
    )
    emit('close')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Upload failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="backdrop" @click.self="emit('close')" @keydown.esc="emit('close')">
    <form
      class="dialog"
      role="dialog"
      aria-modal="true"
      aria-label="Upload bloodwork"
      @submit.prevent="submit"
    >
      <h2>Upload bloodwork PDF</h2>

      <label class="field">
        <span>PDF file</span>
        <input type="file" accept="application/pdf,.pdf" required @change="onFile" />
      </label>
      <label class="field">
        <span>Patient name (optional)</span>
        <input v-model="name" type="text" />
      </label>
      <label class="field">
        <span>Birthday (optional)</span>
        <input v-model="birthday" type="date" />
      </label>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="actions">
        <button type="button" class="btn-secondary" @click="emit('close')">Cancel</button>
        <button type="submit" class="btn-primary" :disabled="!file || submitting">
          {{ submitting ? 'Uploading…' : 'Upload' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 25, 35, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.dialog {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 22px 24px;
  width: 380px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
h2 {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: normal;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}
.field input[type='text'],
.field input[type='date'] {
  font: inherit;
  font-size: 13px;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
}
.error {
  font-size: 12px;
  color: var(--danger);
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.btn-primary {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 7px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-secondary {
  background: none;
  border: 1px solid var(--border);
  padding: 7px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}
</style>
