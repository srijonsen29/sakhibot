import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 45000,
  headers: { 'Content-Type': 'application/json' },
})

// ── request interceptor — attach auth token + log outgoing ──────────────────
client.interceptors.request.use(config => {
  const token = localStorage.getItem('sakhibot_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
  return config
})

// ── response interceptor — log errors ────────────────────────────────────────
client.interceptors.response.use(
  res  => res,
  err  => {
    console.error('[API Error]', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export function saveAuthToken(token) {
  localStorage.setItem('sakhibot_token', token)
}
export function clearAuthToken() {
  localStorage.removeItem('sakhibot_token')
}
export async function signupUser({ name, email, password }) {
  const res = await client.post('/api/auth/signup', {
    name,
    email,
    password,
  })
  return res.data
}
export async function loginUser({ email, password }) {
  const res = await client.post('/api/auth/login', {
    email,
    password,
  })
  return res.data
}
export async function getCurrentUser() {
  const res = await client.get('/api/auth/me')
  return res.data
}

export async function sendMessage({
  message,
  language  = '',
  history   = [],
  district  = '',
  stateName = '',
}) {
  const { data } = await client.post('/api/chat', {
    message,
    language,
    history,
    district,
    state_name: stateName,
  })
  return data
}

export async function downloadDocument({
  documentType,
  history = [],
  language = 'en',
}) {
  const { data } = await client.post(
    '/api/document',
    { document_type: documentType, history, language },
    { responseType: 'blob' }
  )
  return data
}

export async function getLanguages() {
  const { data } = await client.get('/api/languages')
  return data.languages || []
}

export async function healthCheck() {
const { data } = await client.get('/api/health')
  return data
}