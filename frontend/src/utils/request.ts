import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 统一处理响应数据格式
    if (response.data && typeof response.data === 'object') {
      // 如果后端返回的是 { success: true, data: ... } 格式，提取data
      if ('success' in response.data && 'data' in response.data) {
        return { ...response, data: response.data.data }
      }
      // 如果后端返回的是 { success: false, message: ... } 格式，抛出错误
      if ('success' in response.data && !response.data.success) {
        const message = response.data.message || '请求失败'
        ElMessage.error(message)
        return Promise.reject(new Error(message))
      }
    }
    return response
  },
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status
      switch (status) {
        case 400:
          ElMessage.error('请求参数错误')
          break
        case 401:
          ElMessage.error('未授权，请登录')
          // 清除token并跳转到登录页
          localStorage.removeItem('token')
          localStorage.removeItem('userId')
          // 避免循环重定向
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          break
        case 403:
          ElMessage.error('拒绝访问')
          break
        case 404:
          ElMessage.error('请求资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(`请求失败: ${status}`)
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

export default request

