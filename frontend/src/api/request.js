import axios from 'axios'

// 统一 axios 实例: /api 由 vite 代理到后端 8000
const request = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    // 登录失效统一跳转登录页(登录页自身的 401 除外,由页面展示错误)
    if (err.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(err.response?.data || err)
  },
)

// 从 FastAPI 错误体提取可读信息(detail 可能是字符串或 pydantic 校验数组)
export function extractErrMsg(e) {
  if (!e) return '请求失败'
  if (typeof e.detail === 'string') return e.detail
  if (Array.isArray(e.detail) && e.detail[0]?.msg) return e.detail[0].msg
  return '请求失败'
}

export default request
