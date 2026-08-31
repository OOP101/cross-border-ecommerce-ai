import axios from 'axios'
import { ElMessage } from 'element-plus'

export const TOKEN_KEY = 'access_token'
export const ME_KEY = 'me'

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ME_KEY)
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  // 文案全套生成实测可达 90s+（多段真实 LLM 并发），超时放宽到 3 分钟
  timeout: 180000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    // __silent: 调用方自行处理错误（如路由守卫），不弹全局提示
    if (!err.config?.__silent) {
      const msg = err.response?.data?.detail || err.message || '请求失败'
      ElMessage.error(msg)
    }
    // 登录过期：清除本地凭据并回到登录页（避免在登录页循环跳转）
    if (err.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      clearAuth()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
