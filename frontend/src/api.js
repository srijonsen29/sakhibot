import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: BASE,
  timeout: 30000,
})

export async function sendMessage({
  message,
  language = '',
  history = [],
  district = '',
  stateName = '',
}) {
  const res = await client.post('/api/chat', {
    message,
    language,
    history,
    district,
    state_name: stateName,
  })
  return res.data
}

export async function downloadDocument({ documentType, history }) {
  const res = await client.post(
    '/api/document',
    { document_type: documentType, history },
    { responseType: 'blob' }
  )
  return res.data
}

export async function getLanguages() {
  const res = await client.get('/api/languages')
  return res.data.languages
}

export async function healthCheck() {
  const res = await client.get('/api/health')
  return res.data
}