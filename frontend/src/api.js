import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: BASE,
  timeout: 30000,
})

client.interceptors.request.use(config => {
  const token = localStorage.getItem('sakhibot_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

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
