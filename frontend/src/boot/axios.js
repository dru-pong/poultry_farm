import { boot } from 'quasar/wrappers'
import axios from 'axios'

// FIX: Removed trailing space in baseURL (critical for proper API calls)
const api = axios.create({
  baseURL:
    process.env.API_BASE_URL ||
    (process.env.NODE_ENV === 'development'
      ? '/api'
      : 'https://poultry-farm-lzio.onrender.com/api/'),
  withCredentials: true, // THIS IS CRITICAL - sends cookies with requests
})

// Request interceptor to add CSRF token for non-GET requests
api.interceptors.request.use(
  (config) => {
    // Only add CSRF token for requests that modify data
    if (!['get', 'head', 'options'].includes(config.method.toLowerCase())) {
      const csrftoken = document.cookie
        .split(';')
        .find((row) => row.trim().startsWith('csrftoken='))
        ?.split('=')[1]

      if (csrftoken) {
        config.headers['X-CSRFToken'] = csrftoken
      } else {
        console.warn('CSRF token not found in cookies')
      }
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle session expiration automatically
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true

      try {
        // Auto-login with mother's credentials
        await api.post('/auth/login/', {
          username: 'mom', // Use the username you created
          password: 'farm123', // Use the password you set
        })

        // Retry the original request
        return api(error.config)
      } catch (loginError) {
        console.error('Auto-login failed:', loginError)
        return Promise.reject(loginError)
      }
    }

    // Handle network errors (farm internet down)
    if (error.message === 'Network Error' || !error.response) {
      console.log('📶 Farm internet down. Your data will save when connection returns.')

      // For non-GET requests, we'll store the data locally for later sync
      if (!['get', 'head', 'options'].includes(error.config.method.toLowerCase())) {
        try {
          // Store the request data in localStorage for later sync
          const pendingRequests = JSON.parse(localStorage.getItem('pendingRequests') || '[]')
          pendingRequests.push(error.config)
          localStorage.setItem('pendingRequests', JSON.stringify(pendingRequests))

          // Show notification to mother
          if (typeof window !== 'undefined' && window.Quasar) {
            window.Quasar.notify({
              message: '📶 Farm internet down. Changes will save when connection returns.',
              color: 'warning',
              timeout: 3000,
            })
          }
        } catch (e) {
          console.error('Failed to store request:', e)
        }
      }

      // Return empty response to prevent app crashes
      return Promise.resolve({ data: {} })
    }

    return Promise.reject(error)
  },
)

// Check for pending requests when app loads
if (typeof window !== 'undefined') {
  window.addEventListener('load', async () => {
    try {
      const pendingRequests = JSON.parse(localStorage.getItem('pendingRequests') || '[]')

      if (pendingRequests.length > 0) {
        // Try to sync pending requests
        for (const request of pendingRequests) {
          try {
            await api(request)
          } catch (e) {
            console.error('Failed to sync request:', e)
            break // Stop if one fails (connection might still be down)
          }
        }

        // Clear successful requests
        localStorage.setItem('pendingRequests', '[]')

        // Show success notification
        if (typeof window.Quasar !== 'undefined') {
          window.Quasar.notify({
            message: '✅ Synced with farm records server!',
            color: 'positive',
            timeout: 2000,
          })
        }
      }
    } catch (e) {
      console.error('Failed to process pending requests:', e)
    }
  })
}

export default boot(({ app }) => {
  // Make API available throughout the app
  app.config.globalProperties.$api = api
})

export { api }
