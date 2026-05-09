const BASE = '/api'
const H = { 'Content-Type': 'application/json' }

async function req(url, opts = {}) {
  const res = await fetch(url, opts)
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(`${res.status}: ${msg}`)
  }
  if (res.status === 204) return null
  return res.json()
}

// Tasks
export const getTasks  = (p = {}) => req(`${BASE}/tasks?${new URLSearchParams(p)}`)
export const getTask   = (id)     => req(`${BASE}/tasks/${id}`)
export const createTask = (b)     => req(`${BASE}/tasks`, { method: 'POST', headers: H, body: JSON.stringify(b) })
export const updateTask = (id, b) => req(`${BASE}/tasks/${id}`, { method: 'PUT', headers: H, body: JSON.stringify(b) })
export const deleteTask = (id)    => req(`${BASE}/tasks/${id}`, { method: 'DELETE' })
export const runTask    = (id)    => req(`${BASE}/tasks/${id}/run`, { method: 'POST' })
export const duplicateTask = (id) => req(`${BASE}/tasks/${id}/duplicate`, { method: 'POST' })
export const enableTask    = (id) => req(`${BASE}/tasks/${id}/enable`, { method: 'POST' })
export const disableTask   = (id) => req(`${BASE}/tasks/${id}/disable`, { method: 'POST' })

// Script generation
export const generateScript     = (b) => req(`${BASE}/tasks/generate`, { method: 'POST', headers: H, body: JSON.stringify(b) })
export const generateAndCreate  = (b) => req(`${BASE}/tasks/generate-and-create`, { method: 'POST', headers: H, body: JSON.stringify(b) })

// Runs
export const getAllRuns   = (p = {})     => req(`${BASE}/runs?${new URLSearchParams(p)}`)
export const getTaskRuns = (id, p = {}) => req(`${BASE}/tasks/${id}/runs?${new URLSearchParams(p)}`)
export const getRun      = (id)          => req(`${BASE}/runs/${id}`)

// Scheduler
export const getSchedulerStatus = () => req(`${BASE}/scheduler/status`)
export const reloadScheduler    = () => req(`${BASE}/scheduler/reload`, { method: 'POST' })
