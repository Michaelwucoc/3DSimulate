import React, { useRef, useEffect, useState, useCallback } from 'react'
import { Canvas, useThree } from '@react-three/fiber'
import { OrbitControls, Environment, Grid, Stats } from '@react-three/drei'
import * as THREE from 'three'
import { Button } from '../ui/button'
import { Card, CardContent } from '../ui/card'
import { 
  RotateCcw, 
  Move3D, 
  Settings, 
  Camera,
  Maximize,
  Download
} from 'lucide-react'
import { SceneControlsComponent } from './SceneControls'
import { MeasurementTools } from './MeasurementTools'
import { AnnotationTools } from './AnnotationTools'
import ModelLoader from './ModelLoader'
import type { ReconstructionResult, SceneControls, CameraPreset } from '../../types'

interface Scene3DProps {
  result?: ReconstructionResult
  loading?: boolean
  error?: string
  onExport?: (format: string) => void
}

// 相机预设
const CAMERA_PRESETS: CameraPreset[] = [
  {
    id: 'front',
    name: '正视图',
    position: [0, 0, 5],
    target: [0, 0, 0],
    fov: 75
  },
  {
    id: 'back',
    name: '后视图',
    position: [0, 0, -5],
    target: [0, 0, 0],
    fov: 75
  },
  {
    id: 'left',
    name: '左视图',
    position: [-5, 0, 0],
    target: [0, 0, 0],
    fov: 75
  },
  {
    id: 'right',
    name: '右视图',
    position: [5, 0, 0],
    target: [0, 0, 0],
    fov: 75
  },
  {
    id: 'top',
    name: '俯视图',
    position: [0, 5, 0],
    target: [0, 0, 0],
    fov: 75
  },
  {
    id: 'bottom',
    name: '仰视图',
    position: [0, -5, 0],
    target: [0, 0, 0],
    fov: 75
  },
  {
    id: 'isometric',
    name: '等轴测图',
    position: [3, 3, 3],
    target: [0, 0, 0],
    fov: 75
  }
]

// 场景内容组件
function SceneContent({ result }: { result?: ReconstructionResult }) {
  const { camera } = useThree()
  const showStats = false

  // 自动调整相机位置以适应模型
  useEffect(() => {
    if (result?.metadata?.boundingBox) {
      const { min, max } = result.metadata.boundingBox
      const center = new THREE.Vector3(
        (min[0] + max[0]) / 2,
        (min[1] + max[1]) / 2,
        (min[2] + max[2]) / 2
      )
      const size = new THREE.Vector3(
        max[0] - min[0],
        max[1] - min[1],
        max[2] - min[2]
      )
      const maxDim = Math.max(size.x, size.y, size.z)
      const distance = maxDim * 2

      if (camera instanceof THREE.PerspectiveCamera) {
        camera.position.set(center.x + distance, center.y + distance, center.z + distance)
        camera.lookAt(center)
        camera.updateProjectionMatrix()
      }
    }
  }, [result, camera])

  return (
    <>
      {/* 环境光照 */}
      <Environment preset="studio" />
      <ambientLight intensity={0.5} />
      <directionalLight
        position={[10, 10, 5]}
        intensity={1}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />

      {/* 网格 */}
      <Grid
        args={[20, 20]}
        position={[0, -1, 0]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#6f6f6f"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#9d4b4b"
        fadeDistance={30}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid
      />

      {/* 3D模型 */}
      {result?.modelUrl && <ModelLoader result={{ 
        modelUrl: result.modelUrl,
        metadata: result.metadata
      }} />}

      {/* 性能统计 */}
      {showStats && <Stats />}

      {/* 相机控制 */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        dampingFactor={0.05}
        screenSpacePanning={false}
        minDistance={0.1}
        maxDistance={1000}
        maxPolarAngle={Math.PI}
      />
    </>
  )
}

// 主场景组件
export function Scene3D({ result, loading, error }: Scene3DProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const [showMeasurement, setShowMeasurement] = useState(false)
  const [showAnnotation, setShowAnnotation] = useState(false)
  const [sceneControls, setSceneControls] = useState<SceneControls>({
    camera: {
      position: [5, 5, 5],
      rotation: [0, 0, 0],
      fov: 75,
      near: 0.1,
      far: 1000,
      speed: 1.0
    },
    lighting: {
      ambient: 0.4,
      directional: 1.0,
      shadows: true,
      shadowMapSize: 2048
    },
    rendering: {
      quality: 'high',
      antialiasing: true,
      shadows: true,
      toneMapping: true
    },
    helpers: {
      grid: true,
      axes: false,
      stats: false
    }
  })

  // 重置相机
  const resetCamera = useCallback(() => {
    setSceneControls(prev => ({
      ...prev,
      camera: {
        ...prev.camera,
        position: [5, 5, 5],
        rotation: [0, 0, 0]
      }
    }))
  }, [])

  // 应用相机预设
  const applyCameraPreset = useCallback((preset: CameraPreset) => {
    setSceneControls(prev => ({
      ...prev,
      camera: {
        ...prev.camera,
        position: preset.position,
        fov: preset.fov
      }
    }))
  }, [])

  // 全屏切换
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      canvasRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }, [])

  // 监听全屏状态变化
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [])

  // 截图功能
  const takeScreenshot = useCallback(() => {
    if (canvasRef.current) {
      const link = document.createElement('a')
      link.download = `3d-scene-${Date.now()}.png`
      link.href = canvasRef.current.toDataURL()
      link.click()
    }
  }, [])

  if (error) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-destructive text-lg font-semibold mb-2">加载失败</div>
            <div className="text-muted-foreground">{error}</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="relative h-full w-full scene-container">
      {/* 3D画布 */}
      <Canvas
        ref={canvasRef}
        shadows
        camera={{
          position: sceneControls.camera.position,
          fov: sceneControls.camera.fov,
          near: sceneControls.camera.near,
          far: sceneControls.camera.far
        }}
        gl={{
          antialias: sceneControls.rendering.antialiasing,
          toneMapping: sceneControls.rendering.toneMapping ? THREE.ACESFilmicToneMapping : THREE.NoToneMapping
        }}
        className="w-full h-full"
      >
        <SceneContent result={result} />
      </Canvas>

      {/* 加载状态 */}
      {loading && (
        <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <div className="text-lg font-semibold">加载3D模型中...</div>
          </div>
        </div>
      )}

      {/* 工具栏 */}
      <div className="scene-controls">
        <div className="flex flex-col space-y-2">
          {/* 主要控制按钮 */}
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="icon"
              onClick={resetCamera}
              title="重置相机"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="icon"
              onClick={takeScreenshot}
              title="截图"
            >
              <Camera className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="icon"
              onClick={toggleFullscreen}
              title={isFullscreen ? '退出全屏' : '全屏'}
            >
              <Maximize className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="icon"
              onClick={() => setShowControls(!showControls)}
              title="场景设置"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>

          {/* 工具按钮 */}
          <div className="flex space-x-2">
            <Button
              variant={showMeasurement ? "default" : "outline"}
              size="icon"
              onClick={() => setShowMeasurement(!showMeasurement)}
              title="测量工具"
            >
              <Move3D className="h-4 w-4" />
            </Button>
            
            <Button
              variant={showAnnotation ? "default" : "outline"}
              size="icon"
              onClick={() => setShowAnnotation(!showAnnotation)}
              title="标注工具"
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>

          {/* 相机预设 */}
          <div className="bg-white/90 backdrop-blur-sm rounded-lg p-2 max-w-xs">
            <div className="text-xs font-semibold mb-2">相机预设</div>
            <div className="grid grid-cols-2 gap-1">
              {CAMERA_PRESETS.map((preset) => (
                <Button
                  key={preset.id}
                  variant="ghost"
                  size="sm"
                  onClick={() => applyCameraPreset(preset)}
                  className="text-xs h-8"
                >
                  {preset.name}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 场景控制面板 */}
      {showControls && (
        <div className="absolute top-4 left-4 z-10">
          <SceneControlsComponent
            controls={sceneControls}
            onChange={setSceneControls}
            onClose={() => setShowControls(false)}
          />
        </div>
      )}

      {/* 测量工具 */}
      {showMeasurement && (
        <div className="absolute bottom-4 left-4 z-10">
          <MeasurementTools
            onClose={() => setShowMeasurement(false)}
          />
        </div>
      )}

      {/* 标注工具 */}
      {showAnnotation && (
        <div className="absolute bottom-4 right-4 z-10">
          <AnnotationTools
            onClose={() => setShowAnnotation(false)}
          />
        </div>
      )}

      {/* 模型信息 */}
      {result && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10">
          <Card className="bg-white/90 backdrop-blur-sm">
            <CardContent className="p-3">
              <div className="text-xs space-y-1">
                <div>格式: {result.format?.toUpperCase() || 'N/A'}</div>
                <div>顶点: {result.metadata?.vertices?.toLocaleString() || 'N/A'}</div>
                {result.metadata?.faces && (
                  <div>面: {result.metadata.faces.toLocaleString()}</div>
                )}
                <div>质量: {result.statistics?.quality || 'N/A'}</div>
                <div>方法: {result.statistics?.method?.toUpperCase() || 'N/A'}</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}