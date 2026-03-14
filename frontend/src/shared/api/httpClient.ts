import axios from 'axios'

const DEFAULT_API_URL = 'http://localhost:8000'
const configuredApiUrl = import.meta.env.VITE_API_URL?.trim()

export const httpClient = axios.create({
  baseURL: configuredApiUrl && configuredApiUrl.length > 0 ? configuredApiUrl : DEFAULT_API_URL,
  timeout: 10000,
})
