import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import * as THREE from 'three'

// Tailwind CSS 类名合并工具
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 文件大小格式化
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 验证视频文件
export function isValidVideoFile(file: File): boolean {
  const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm']
  return validTypes.includes(file.type)
}

// 验证图片文件
export function isValidImageFile(file: File): boolean {
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp']
  return validTypes.includes(file.type)
}

// 生成唯一ID
export function generateId(): string {
  return Math.random().toString(36).substr(2, 9) + Date.now().toString(36)
}

// 防抖函数
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// 节流函数
export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// 3D坐标转换为屏幕坐标
export function worldToScreen(
  position: THREE.Vector3,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer
): { x: number; y: number } {
  const vector = position.clone()
  vector.project(camera)
  
  const canvas = renderer.domElement
  const x = (vector.x * 0.5 + 0.5) * canvas.clientWidth
  const y = (vector.y * -0.5 + 0.5) * canvas.clientHeight
  
  return { x, y }
}

// 屏幕坐标转换为3D坐标
export function screenToWorld(
  x: number,
  y: number,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer
): THREE.Vector3 {
  const canvas = renderer.domElement
  const mouse = new THREE.Vector2(
    (x / canvas.clientWidth) * 2 - 1,
    -(y / canvas.clientHeight) * 2 + 1
  )
  
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(mouse, camera)
  
  return raycaster.ray.direction
}

// 计算两点间距离
export function calculateDistance(
  point1: [number, number, number],
  point2: [number, number, number]
): number {
  const dx = point2[0] - point1[0]
  const dy = point2[1] - point1[1]
  const dz = point2[2] - point1[2]
  return Math.sqrt(dx * dx + dy * dy + dz * dz)
}

// 计算三点间角度
export function calculateAngle(
  point1: [number, number, number],
  vertex: [number, number, number],
  point2: [number, number, number]
): number {
  const v1 = new THREE.Vector3(
    point1[0] - vertex[0],
    point1[1] - vertex[1],
    point1[2] - vertex[2]
  )
  const v2 = new THREE.Vector3(
    point2[0] - vertex[0],
    point2[1] - vertex[1],
    point2[2] - vertex[2]
  )
  
  return v1.angleTo(v2) * (180 / Math.PI)
}

// 颜色转换工具
export function hexToRgb(hex: string): [number, number, number] | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? [
    parseInt(result[1], 16) / 255,
    parseInt(result[2], 16) / 255,
    parseInt(result[3], 16) / 255
  ] : null
}

// RGB转十六进制
export function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) => {
    const hex = Math.round(n * 255).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

// 时间格式化
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// 错误处理工具
export function handleError(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return '未知错误'
}

// 深拷贝
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime()) as T
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as T
  }
  
  if (typeof obj === 'object') {
    const cloned = {} as T
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        cloned[key] = deepClone(obj[key])
      }
    }
    return cloned
  }
  
  return obj
}

// 本地存储工具
export const storage = {
  get<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue ?? null
    } catch {
      return defaultValue ?? null
    }
  },
  
  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('Failed to save to localStorage:', error)
    }
  },
  
  remove(key: string): void {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Failed to remove from localStorage:', error)
    }
  },
  
  clear(): void {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Failed to clear localStorage:', error)
    }
  }
}

// 文件下载工具
export function downloadFile(data: Blob | string, filename: string, type?: string): void {
  const blob = data instanceof Blob ? data : new Blob([data], { type: type || 'text/plain' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// 异步延迟
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// 重试机制
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delayMs: number = 1000
): Promise<T> {
  let lastError: Error
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))
      
      if (attempt === maxAttempts) {
        throw lastError
      }
      
      await delay(delayMs * attempt)
    }
  }
  
  throw lastError!
}