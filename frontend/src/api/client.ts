import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: { Accept: 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config
  if (error.response?.status === 401 && !original?._retried && localStorage.getItem('refresh_token')) {
    original._retried = true
    try {
      const { data } = await axios.post(`${api.defaults.baseURL}/accounts/refresh/`, { refresh_token: localStorage.getItem('refresh_token') })
      localStorage.setItem('access_token', data.access_token)
      original.headers.Authorization = `Bearer ${data.access_token}`
      return api(original)
    } catch {
      localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token')
      window.dispatchEvent(new Event('auth:expired'))
    }
  }
  return Promise.reject(error)
})
