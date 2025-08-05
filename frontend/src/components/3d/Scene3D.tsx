import React, { useRef, useState, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Environment, Stats } from '@react-three/drei'
import { ReconstructionResult } from '../../types'
import { ModelLoader } from './ModelLoader'
import { SceneControls } from './SceneControls'
import { MeasurementTools } from './MeasurementTools'
import { AnnotationTools } from './AnnotationTools'

interface Scene3DProps {
  modelData?: ReconstructionResult
  onSceneReady?: () => void
}

function SceneContent({ modelData, onSceneReady }: Scene3DProps) {
  const { camera, scene } = useThree()
  const [isModelLoaded, setIsModelLoaded] = useState(false)

  // 初始化相机位置
  useEffect(() => {
    if (modelData?.metadata?.cameraPositions?.[0]) {
      const camPos = modelData.metadata.cameraPositions[0]
      camera.position.set(...camPos.position)
      camera.lookAt(0, 0, 0)
    } else {
      // 默认相机位置
      camera.position.set(5, 5, 5)
      camera.lookAt(0, 0, 0)
    }
  }, [camera, modelData])

  // 设置环境光
  useEffect(() => {
    scene.background = null // 透明背景
  }, [scene])

  const handleModelLoaded = () => {
    setIsModelLoaded(true)
    onSceneReady?.()
  }

  return (
    <>
      {/* 环境光 */}
      <ambientLight intensity={0.4} />
      
      {/* 方向光 */}
      <directionalLight
        position={[10, 10, 5]}
        intensity={1}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />

      {/* 模型加载器 */}
      {modelData && (
        <ModelLoader
          modelUrl={modelData.modelUrl}
          onLoad={handleModelLoaded}
        />
      )}

      {/* 测量工具 */}
      <MeasurementTools />

      {/* 标注工具 */}
      <AnnotationTools />

      {/* 相机控制 */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        maxDistance={50}
        minDistance={0.5}
        dampingFactor={0.05}
        dampingInertiaRatio={0.9}
      />

      {/* 环境 */}
      <Environment preset="apartment" />
    </>
  )
}

export function Scene3D({ modelData, onSceneReady }: Scene3DProps) {
  const [showStats, setShowStats] = useState(false)
  const [showControls, setShowControls] = useState(true)

  return (
    <div className="relative w-full h-full">
      {/* 3D场景画布 */}
      <Canvas
        shadows
        camera={{ fov: 75, near: 0.1, far: 1000 }}
        gl={{ 
          antialias: true,
          alpha: true,
          preserveDrawingBuffer: true
        }}
        className="scene-container"
      >
        <SceneContent 
          modelData={modelData} 
          onSceneReady={onSceneReady} 
        />
        
        {/* 性能统计 */}
        {showStats && <Stats />}
      </Canvas>

      {/* 控制面板 */}
      {showControls && (
        <SceneControls
          onToggleStats={() => setShowStats(!showStats)}
          onToggleControls={() => setShowControls(!showControls)}
        />
      )}

      {/* 加载状态 */}
      {!modelData && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm">
          <div className="text-center text-white">
            <div className="loading-spinner w-8 h-8 border-4 border-white border-t-transparent rounded-full mx-auto mb-4"></div>
            <p>等待3D模型加载...</p>
          </div>
        </div>
      )}
    </div>
  )
} 