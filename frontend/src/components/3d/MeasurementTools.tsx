import React, { useState, useRef } from 'react'
import { useThree, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Measurement } from '../../types'

interface MeasurementToolsProps {
  measurements?: Measurement[]
  onMeasurementAdd?: (measurement: Measurement) => void
  onMeasurementRemove?: (id: string) => void
}

export function MeasurementTools({ 
  measurements = [], 
  onMeasurementAdd, 
  onMeasurementRemove 
}: MeasurementToolsProps) {
  const { camera, raycaster, mouse, gl } = useThree()
  const [isActive, setIsActive] = useState(false)
  const [currentPoints, setCurrentPoints] = useState<THREE.Vector3[]>([])
  const [hoveredPoint, setHoveredPoint] = useState<THREE.Vector3 | null>(null)

  // 鼠标点击处理
  const handleClick = () => {
    if (!isActive) return

    if (currentPoints.length < 2) {
      // 添加新点
      if (hoveredPoint) {
        setCurrentPoints(prev => [...prev, hoveredPoint.clone()])
      }
    } else {
      // 完成测量
      if (onMeasurementAdd && currentPoints.length >= 2) {
        const distance = currentPoints[0].distanceTo(currentPoints[1])
        const measurement: Measurement = {
          id: Math.random().toString(36).substr(2, 9),
          type: 'distance',
          points: currentPoints.map(p => [p.x, p.y, p.z]),
          value: distance,
          unit: 'm',
          color: '#ff0000'
        }
        onMeasurementAdd(measurement)
      }
      setCurrentPoints([])
    }
  }

  // 鼠标移动处理
  useFrame(() => {
    if (!isActive) return

    // 更新鼠标位置
    raycaster.setFromCamera(mouse, camera)

    // 检测与场景中物体的交点
    const intersects = raycaster.intersectObjects(gl.scene.children, true)
    
    if (intersects.length > 0) {
      setHoveredPoint(intersects[0].point)
    } else {
      setHoveredPoint(null)
    }
  })

  // 计算两点间距离
  const calculateDistance = (point1: THREE.Vector3, point2: THREE.Vector3): number => {
    return point1.distanceTo(point2)
  }

  // 计算三点间角度
  const calculateAngle = (point1: THREE.Vector3, point2: THREE.Vector3, point3: THREE.Vector3): number => {
    const v1 = point1.clone().sub(point2)
    const v2 = point3.clone().sub(point2)
    return v1.angleTo(v2) * (180 / Math.PI)
  }

  return (
    <>
      {/* 当前测量点 */}
      {currentPoints.map((point, index) => (
        <mesh key={index} position={point}>
          <sphereGeometry args={[0.05, 16, 16]} />
          <meshBasicMaterial color="#ff0000" />
        </mesh>
      ))}

      {/* 悬停点 */}
      {hoveredPoint && (
        <mesh position={hoveredPoint}>
          <sphereGeometry args={[0.03, 16, 16]} />
          <meshBasicMaterial color="#00ff00" />
        </mesh>
      )}

      {/* 测量线 */}
      {currentPoints.length >= 1 && hoveredPoint && (
        <line>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([
                currentPoints[0].x, currentPoints[0].y, currentPoints[0].z,
                hoveredPoint.x, hoveredPoint.y, hoveredPoint.z
              ])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#ff0000" />
        </line>
      )}

      {/* 已完成的测量 */}
      {measurements.map(measurement => (
        <MeasurementDisplay
          key={measurement.id}
          measurement={measurement}
          onRemove={() => onMeasurementRemove?.(measurement.id)}
        />
      ))}
    </>
  )
}

// 测量显示组件
interface MeasurementDisplayProps {
  measurement: Measurement
  onRemove?: () => void
}

function MeasurementDisplay({ measurement, onRemove }: MeasurementDisplayProps) {
  const { camera } = useThree()
  const [isVisible, setIsVisible] = useState(true)

  if (!isVisible) return null

  return (
    <group>
      {/* 测量点 */}
      {measurement.points.map((point, index) => (
        <mesh key={index} position={new THREE.Vector3(...point)}>
          <sphereGeometry args={[0.05, 16, 16]} />
          <meshBasicMaterial color={measurement.color} />
        </mesh>
      ))}

      {/* 测量线 */}
      {measurement.points.length >= 2 && (
        <line>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={measurement.points.length}
              array={new Float32Array(measurement.points.flat())}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color={measurement.color} />
        </line>
      )}

      {/* 测量标签 */}
      {measurement.points.length >= 2 && (
        <MeasurementLabel
          measurement={measurement}
          onRemove={onRemove}
        />
      )}
    </group>
  )
}

// 测量标签组件
interface MeasurementLabelProps {
  measurement: Measurement
  onRemove?: () => void
}

function MeasurementLabel({ measurement, onRemove }: MeasurementLabelProps) {
  const { camera } = useThree()
  
  // 计算标签位置（两点中点）
  const midPoint = new THREE.Vector3()
  if (measurement.points.length >= 2) {
    const p1 = new THREE.Vector3(...measurement.points[0])
    const p2 = new THREE.Vector3(...measurement.points[1])
    midPoint.lerpVectors(p1, p2, 0.5)
  }

  return (
    <group position={midPoint}>
      {/* 这里可以添加HTML标签显示测量值 */}
      {/* 由于Three.js的限制，实际标签需要通过HTML overlay实现 */}
    </group>
  )
} 