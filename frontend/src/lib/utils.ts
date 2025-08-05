import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 文件大小格式化
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 文件类型检查
export function isValidVideoFile(file: File): boolean {
  const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv', 'video/webm']
  return validTypes.includes(file.type)
}

export function isValidImageFile(file: File): boolean {
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  return validTypes.includes(file.type)
}

// 生成唯一ID
export function generateId(): string {
  return Math.random().toString(36).substr(2, 9)
}

// 防抖函数
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// 节流函数
export function throttle<T extends (...args: any[]) => any>(
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

// 3D坐标转换
export function worldToScreen(
  worldPos: [number, number, number],
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer
): [number, number] {
  const vector = new THREE.Vector3(...worldPos)
  vector.project(camera)
  
  const x = (vector.x * 0.5 + 0.5) * renderer.domElement.clientWidth
  const y = (-vector.y * 0.5 + 0.5) * renderer.domElement.clientHeight
  
  return [x, y]
}

// 屏幕坐标转世界坐标
export function screenToWorld(
  screenPos: [number, number],
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  distance: number = 10
): [number, number, number] {
  const vector = new THREE.Vector3()
  
  vector.x = (screenPos[0] / renderer.domElement.clientWidth) * 2 - 1
  vector.y = -(screenPos[1] / renderer.domElement.clientHeight) * 2 + 1
  vector.z = 0.5
  
  vector.unproject(camera)
  vector.setLength(distance)
  
  return [vector.x, vector.y, vector.z]
} 