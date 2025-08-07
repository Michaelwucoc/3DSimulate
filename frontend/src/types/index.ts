// 文件上传相关类型
export interface UploadFile {
  id: string
  name: string
  size: number
  type: 'video' | 'image'
  file: File
  preview?: string
  uploadedAt: Date
  progress?: number
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
  method: 'nerf' | '3dgs' // NeRF 或 3D Gaussian Splatting
}

// 3D重建结果
export interface ReconstructionResult {
  modelUrl?: string
  thumbnailUrl?: string
  model_path?: string
  thumbnail_path?: string
  metadata_path?: string
  point_cloud_path?: string
  mesh_path?: string
  texture_path?: string
  num_points?: number
  num_faces?: number
  model_size_mb?: number
  psnr?: number
  ssim?: number
  lpips?: number
  render_config?: Record<string, unknown>
  export_formats?: string[]
  // 兼容旧格式
  format?: 'ply' | 'obj' | 'gltf' | 'splat'
  metadata?: {
    vertices?: number
    faces?: number
    points?: number
    boundingBox?: {
      min: [number, number, number]
      max: [number, number, number]
    }
    cameraPositions?: Array<{
      position: [number, number, number]
      rotation: [number, number, number]
      fov: number
    }>
  }
  statistics?: {
    processingTime?: number
    memoryUsage?: number
    quality?: 'low' | 'medium' | 'high'
    method?: 'nerf' | '3dgs'
  }
}

// 3D场景控制
export interface SceneControls {
  camera: {
    position: [number, number, number]
    rotation: [number, number, number]
    fov: number
    near: number
    far: number
    speed: number
  }
  lighting: {
    ambient: number
    directional: number
    shadows: boolean
    shadowMapSize: number
  }
  rendering: {
    quality: 'low' | 'medium' | 'high'
    antialiasing: boolean
    shadows: boolean
    toneMapping: boolean
  }
  helpers: {
    grid: boolean
    axes: boolean
    stats: boolean
  }
}

// 测量工具
export interface Measurement {
  id: string
  type: 'distance' | 'angle' | 'area' | 'volume'
  points: Array<[number, number, number]>
  value: number
  unit: string
  color: string
  label?: string
  visible: boolean
}

// 标注工具
export interface Annotation {
  id: string
  position: [number, number, number]
  text: string
  color: string
  visible: boolean
  type: 'point' | 'text' | 'arrow'
  size: number
}

// 相机预设
export interface CameraPreset {
  id: string
  name: string
  position: [number, number, number]
  target: [number, number, number]
  fov: number
  description?: string
}

// API响应类型
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
  message?: string
  timestamp: string
}

// 上传响应
export interface UploadResponse {
  task_id: string
  files: Array<{
    id: string
    name: string
    url: string
    size: number
  }>
}

// 任务状态响应
export interface TaskStatusResponse {
  taskId: string
  status: ReconstructionTask['status']
  progress: number
  message: string
  result?: ReconstructionResult
  estimatedTimeRemaining?: number
}

// 3D模型数据
export interface ModelData {
  vertices: Float32Array
  indices?: Uint32Array
  normals: Float32Array
  uvs?: Float32Array
  colors?: Float32Array
  materials?: Array<{
    name: string
    diffuse: [number, number, number]
    specular: [number, number, number]
    shininess: number
    textureUrl?: string
    opacity?: number
  }>
}

// Gaussian Splatting 特定数据
export interface GaussianSplattingData {
  positions: Float32Array
  rotations: Float32Array
  scales: Float32Array
  colors: Float32Array
  opacities: Float32Array
  count: number
}

// NeRF 特定数据
export interface NeRFData {
  networkWeights: ArrayBuffer
  boundingBox: {
    min: [number, number, number]
    max: [number, number, number]
  }
  resolution: [number, number, number]
  viewDependency: boolean
}

// 用户设置
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto'
  language: 'zh' | 'en'
  quality: 'low' | 'medium' | 'high'
  autoSave: boolean
  shortcuts: Record<string, string>
  defaultMethod: 'nerf' | '3dgs'
  maxFileSize: number // MB
  maxFiles: number
}

// 项目配置
export interface ProjectConfig {
  name: string
  description?: string
  createdAt: Date
  updatedAt: Date
  tasks: ReconstructionTask[]
  settings: UserSettings
}

// 导出格式选项
export interface ExportOptions {
  format: 'ply' | 'obj' | 'gltf' | 'fbx' | 'stl'
  quality: 'low' | 'medium' | 'high'
  includeTextures: boolean
  includeAnimations: boolean
  compression: boolean
}

// 性能监控
export interface PerformanceMetrics {
  fps: number
  memoryUsage: number
  renderTime: number
  triangleCount: number
  drawCalls: number
}