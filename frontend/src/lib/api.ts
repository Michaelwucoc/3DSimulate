import type { 
  ReconstructionTask, 
  ApiResponse, 
  UploadResponse, 
  TaskStatusResponse 
} from '../types'

// API基础配置
const API_BASE_URL = 'http://127.0.0.1:8000/api'

// HTTP请求工具类
class ApiClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, { ...defaultOptions, ...options })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return {
        success: true,
        data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      console.error('API request failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      }
    }
  }

  // GET请求
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  // POST请求
  async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // PUT请求
  async put<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // DELETE请求
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  // 文件上传
  async uploadFiles(files: File[]): Promise<ApiResponse<UploadResponse>> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append(`files`, file)
    })

    const url = `${this.baseURL}/upload`
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed! status: ${response.status}`)
      }

      const data = await response.json()
      return {
        success: true,
        data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      console.error('File upload failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Upload failed',
        timestamp: new Date().toISOString()
      }
    }
  }
}

// 创建API客户端实例
const apiClient = new ApiClient(API_BASE_URL)

// API服务函数
export const api = {
  // 健康检查
  async health() {
    return apiClient.get('/health')
  },

  // 文件上传
  async uploadFiles(files: File[]): Promise<ApiResponse<UploadResponse>> {
    return apiClient.uploadFiles(files)
  },

  // 获取所有任务
  async getTasks(): Promise<ApiResponse<ReconstructionTask[]>> {
    return apiClient.get('/tasks')
  },

  // 获取任务状态
  async getTaskStatus(taskId: string): Promise<ApiResponse<TaskStatusResponse>> {
    return apiClient.get(`/tasks/${taskId}/status`)
  },

  // 开始3D重建任务
  async startReconstruction(taskId: string, method: 'nerf' | '3dgs'): Promise<ApiResponse<{ message: string }>> {
    return apiClient.post(`/tasks/${taskId}/start`, { method })
  },

  // 删除任务
  async deleteTask(taskId: string): Promise<ApiResponse<{ message: string }>> {
    return apiClient.delete(`/tasks/${taskId}`)
  },

  // 下载结果
  async downloadResult(taskId: string, format: string): Promise<ApiResponse<Blob>> {
    const url = `${API_BASE_URL}/tasks/${taskId}/download?format=${format}`
    
    try {
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`Download failed! status: ${response.status}`)
      }

      const blob = await response.blob()
      return {
        success: true,
        data: blob,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      console.error('Download failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Download failed',
        timestamp: new Date().toISOString()
      }
    }
  },

  // 获取系统信息
  async getSystemInfo(): Promise<ApiResponse<{
    gpu_available: boolean
    memory_usage: number
    disk_usage: number
    active_tasks: number
  }>> {
    return apiClient.get('/system/info')
  }
}

// 导出API客户端
export { apiClient }
export default api