import { API_BASE_URL } from '../config'
import type { BloodworkResponse } from '../types/bloodwork'

// Failed HTTP response, carrying the backend's `detail` message when it sent one.
class ApiError extends Error {}

async function errorFromResponse(response: Response, fallback: string): Promise<ApiError> {
  try {
    const payload = await response.json()
    if (typeof payload.detail === 'string') return new ApiError(payload.detail)
  } catch {
    // body wasn't JSON; use the generic message below
  }
  return new ApiError(`${fallback} (${response.status})`)
}

// Message to show the user for anything thrown by this module.
export function describeError(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof TypeError) return 'Cannot reach the server'
  return 'Unknown error'
}

export async function getResults(
  start: string,
  end: string,
  signal?: AbortSignal,
): Promise<BloodworkResponse> {
  const params = new URLSearchParams({ start_date: start, end_date: end })
  const response = await fetch(`${API_BASE_URL}/results?${params}`, { signal })
  if (!response.ok) throw await errorFromResponse(response, 'Could not load results')
  return response.json()
}

export interface UploadMetadata {
  name?: string
  birthday?: string // DD/MM/YYYY
}

export async function uploadBloodwork(file: File, { name, birthday }: UploadMetadata = {}) {
  const body = new FormData()
  body.append('file', file)
  if (name?.trim()) body.append('name', name.trim())
  if (birthday) body.append('birthday', birthday)

  const response = await fetch(`${API_BASE_URL}/upload-bloodwork`, { method: 'POST', body })
  if (!response.ok) throw await errorFromResponse(response, 'Upload failed')
}
