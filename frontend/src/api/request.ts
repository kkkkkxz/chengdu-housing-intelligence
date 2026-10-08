import axios from "axios";

const request = axios.create({
  baseURL: '/api',
  timeout: 1000000
})

request.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem('token')
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (e) {
      // ignore storage errors
    }

    // 当上传 FormData 时，交由浏览器自动设置 multipart 边界
    if (config.data instanceof FormData && config.headers) {
      delete (config.headers as any)['Content-Type']
    } else if (config.headers && !(config.headers as any)['Content-Type']) {
      ;(config.headers as any)['Content-Type'] = 'application/json'
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    try {
      if (error.response?.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        window.location.href = '/login'
      }
    } catch (e) {
      // ignore
    }
    return Promise.reject(error)
  }
)

export default request