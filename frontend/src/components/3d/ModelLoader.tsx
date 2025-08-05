import React, { useRef, useEffect, useState } from 'react'
import { useLoader, useFrame } from '@react-three/fiber'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader'
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader'
import * as THREE from 'three'

interface ModelLoaderProps {
  modelUrl: string
  onLoad?: () => void
  onError?: (error: string) => void
}

export function ModelLoader({ modelUrl, onLoad, onError }: ModelLoaderProps) {
  const [model, setModel] = useState<THREE.Group | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!modelUrl) return

    setLoading(true)
    setError(null)

    const loadModel = async () => {
      try {
        let loadedModel: THREE.Group

        // 根据文件扩展名选择加载器
        const fileExtension = modelUrl.split('.').pop()?.toLowerCase()

        switch (fileExtension) {
          case 'gltf':
          case 'glb':
            // 使用GLTF加载器
            const gltfLoader = new GLTFLoader()
            
            // 设置DRACO解码器（如果可用）
            const dracoLoader = new DRACOLoader()
            dracoLoader.setDecoderPath('/draco/')
            gltfLoader.setDRACOLoader(dracoLoader)
            
            const gltf = await new Promise<THREE.GLTF>((resolve, reject) => {
              gltfLoader.load(modelUrl, resolve, undefined, reject)
            })
            loadedModel = gltf.scene
            break

          case 'obj':
            // 使用OBJ加载器
            const objLoader = new OBJLoader()
            loadedModel = await new Promise<THREE.Group>((resolve, reject) => {
              objLoader.load(modelUrl, resolve, undefined, reject)
            })
            break

          case 'ply':
            // 使用PLY加载器
            const plyLoader = new PLYLoader()
            const geometry = await new Promise<THREE.BufferGeometry>((resolve, reject) => {
              plyLoader.load(modelUrl, resolve, undefined, reject)
            })
            
            // 创建材质和网格
            const material = new THREE.MeshStandardMaterial({
              color: 0xcccccc,
              side: THREE.DoubleSide
            })
            const mesh = new THREE.Mesh(geometry, material)
            loadedModel = new THREE.Group()
            loadedModel.add(mesh)
            break

          default:
            throw new Error(`不支持的文件格式: ${fileExtension}`)
        }

        // 处理加载的模型
        processModel(loadedModel)
        setModel(loadedModel)
        setLoading(false)
        onLoad?.()

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '模型加载失败'
        setError(errorMessage)
        setLoading(false)
        onError?.(errorMessage)
      }
    }

    loadModel()
  }, [modelUrl, onLoad, onError])

  // 处理模型（居中、缩放等）
  const processModel = (model: THREE.Group) => {
    // 计算包围盒
    const box = new THREE.Box3().setFromObject(model)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())

    // 居中模型
    model.position.sub(center)

    // 缩放模型到合适大小
    const maxSize = Math.max(size.x, size.y, size.z)
    const scale = 5 / maxSize // 缩放到5个单位
    model.scale.setScalar(scale)

    // 遍历所有网格，设置材质属性
    model.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        // 启用阴影
        child.castShadow = true
        child.receiveShadow = true

        // 如果材质存在，设置一些默认属性
        if (child.material) {
          if (Array.isArray(child.material)) {
            child.material.forEach(mat => {
              if (mat instanceof THREE.Material) {
                mat.needsUpdate = true
              }
            })
          } else {
            child.material.needsUpdate = true
          }
        }
      }
    })
  }

  // 渲染模型
  if (loading) {
    return null // 加载时显示加载状态
  }

  if (error || !model) {
    return null // 错误时不渲染
  }

  return <primitive object={model} />
}

// 用于加载GLTF模型的Hook
export function useGLTFModel(url: string) {
  const gltf = useLoader(GLTFLoader, url)
  return gltf
}

// 用于加载OBJ模型的Hook
export function useOBJModel(url: string) {
  const obj = useLoader(OBJLoader, url)
  return obj
} 