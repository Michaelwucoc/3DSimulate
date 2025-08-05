// 文件上传相关类型
export interface UploadFile {
  id: string
  name: string
  size: number
  type: 'video' | 'image'
  file: File
  preview?: string
  uploadedAt: Date
}

// 3D重建任务状态
export interface ReconstructionTask {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  files: UploadFile[]
  createdAt: Date
  completedAt?: Date
  result?: ReconstructionResult
}

// 3D重建结果
export interface ReconstructionResult {
  id: string
  modelUrl: string
  thumbnailUrl: string
  metadata: {
    vertices: number
    faces: number
    boundingBox: {
      min: [number, number, number]
      max: [number, number, number]
    }
    cameraPositions: Array<{
      position: [number, number, number]
      rotation: [number, number, number]
    }>
  }
  statistics: {
    processingTime: number
    memoryUsage: number
    quality: 'low' | 'medium' | 'high'
  }
}

// 3D场景控制
export interface SceneControls {
  camera: {
    position: [number, number, number]
    rotation: [number, number, number]
    fov: number
  }
  lighting: {
    ambient: number
    directional: number
    shadows: boolean
  }
  rendering: {
    quality: 'low' | 'medium' | 'high'
    antialiasing: boolean
    shadows: boolean
  }
}

// 测量工具
export interface Measurement {
  id: string
  type: 'distance' | 'angle' | 'area'
  points: Array<[number, number, number]>
  value: number
  unit: string
  color: string
}

// 标注工具
export interface Annotation {
  id: string
  position: [number, number, number]
  text: string
  color: string
  visible: boolean
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// 上传响应
export interface UploadResponse {
  taskId: string
  files: Array<{
    id: string
    name: string
    url: string
  }>
}

// 任务状态响应
export interface TaskStatusResponse {
  taskId: string
  status: ReconstructionTask['status']
  progress: number
  message: string
  result?: ReconstructionResult
}

// 3D模型数据
export interface ModelData {
  vertices: Float32Array
  indices: Uint32Array
  normals: Float32Array
  uvs: Float32Array
  materials: Array<{
    name: string
    diffuse: [number, number, number]
    specular: [number, number, number]
    shininess: number
    textureUrl?: string
  }>
}

// 相机预设
export interface CameraPreset {
  id: string
  name: string
  position: [number, number, number]
  target: [number, number, number]
  fov: number
}

// 用户设置
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto'
  language: string
  quality: 'low' | 'medium' | 'high'
  autoSave: boolean
  shortcuts: Record<string, string>
} 