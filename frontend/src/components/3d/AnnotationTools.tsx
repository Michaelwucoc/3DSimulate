import React, { useState, useRef } from 'react'
import { useThree, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Annotation } from '../../types'

interface AnnotationToolsProps {
  annotations?: Annotation[]
  onAnnotationAdd?: (annotation: Annotation) => void
  onAnnotationRemove?: (id: string) => void
  onAnnotationUpdate?: (id: string, annotation: Partial<Annotation>) => void
}

export function AnnotationTools({
  annotations = [],
  onAnnotationAdd,
  onAnnotationRemove,
  onAnnotationUpdate
}: AnnotationToolsProps) {
  const { camera, raycaster, mouse, gl } = useThree()
  const [isActive, setIsActive] = useState(false)
  const [hoveredPoint, setHoveredPoint] = useState<THREE.Vector3 | null>(null)
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null)

  // 鼠标点击处理
  const handleClick = () => {
    if (!isActive || !hoveredPoint) return

    // 创建新标注
    const annotation: Annotation = {
      id: Math.random().toString(36).substr(2, 9),
      position: [hoveredPoint.x, hoveredPoint.y, hoveredPoint.z],
      text: `标注 ${annotations.length + 1}`,
      color: '#ffff00',
      visible: true
    }

    onAnnotationAdd?.(annotation)
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

  return (
    <>
      {/* 悬停点指示器 */}
      {isActive && hoveredPoint && (
        <mesh position={hoveredPoint}>
          <sphereGeometry args={[0.03, 16, 16]} />
          <meshBasicMaterial color="#ffff00" />
        </mesh>
      )}

      {/* 标注点 */}
      {annotations.map(annotation => (
        <AnnotationMarker
          key={annotation.id}
          annotation={annotation}
          isSelected={selectedAnnotation === annotation.id}
          onSelect={() => setSelectedAnnotation(annotation.id)}
          onRemove={() => onAnnotationRemove?.(annotation.id)}
          onUpdate={(updates) => onAnnotationUpdate?.(annotation.id, updates)}
        />
      ))}
    </>
  )
}

// 标注标记组件
interface AnnotationMarkerProps {
  annotation: Annotation
  isSelected: boolean
  onSelect: () => void
  onRemove: () => void
  onUpdate: (updates: Partial<Annotation>) => void
}

function AnnotationMarker({
  annotation,
  isSelected,
  onSelect,
  onRemove,
  onUpdate
}: AnnotationMarkerProps) {
  const { camera } = useThree()
  const [isHovered, setIsHovered] = useState(false)

  if (!annotation.visible) return null

  const position = new THREE.Vector3(...annotation.position)

  return (
    <group position={position}>
      {/* 标注点 */}
      <mesh
        onClick={onSelect}
        onPointerOver={() => setIsHovered(true)}
        onPointerOut={() => setIsHovered(false)}
      >
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshBasicMaterial 
          color={isSelected ? '#ff0000' : annotation.color}
          transparent
          opacity={isHovered ? 0.8 : 0.6}
        />
      </mesh>

      {/* 选中状态指示器 */}
      {isSelected && (
        <mesh>
          <ringGeometry args={[0.08, 0.12, 16]} />
          <meshBasicMaterial color="#ff0000" side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* 标注线（连接到地面或物体表面） */}
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={2}
            array={new Float32Array([
              position.x, position.y, position.z,
              position.x, position.y - 0.5, position.z
            ])}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color={annotation.color} />
      </line>
    </group>
  )
}

// 标注标签组件（HTML overlay）
interface AnnotationLabelProps {
  annotation: Annotation
  screenPosition: [number, number]
  onUpdate: (text: string) => void
  onRemove: () => void
}

export function AnnotationLabel({
  annotation,
  screenPosition,
  onUpdate,
  onRemove
}: AnnotationLabelProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [text, setText] = useState(annotation.text)

  const handleSave = () => {
    onUpdate(text)
    setIsEditing(false)
  }

  const handleCancel = () => {
    setText(annotation.text)
    setIsEditing(false)
  }

  return (
    <div
      className="absolute bg-white border border-gray-300 rounded-lg shadow-lg p-2 min-w-[120px]"
      style={{
        left: screenPosition[0],
        top: screenPosition[1],
        transform: 'translate(-50%, -100%)',
        zIndex: 1000
      }}
    >
      {isEditing ? (
        <div className="space-y-2">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
            autoFocus
          />
          <div className="flex space-x-1">
            <button
              onClick={handleSave}
              className="px-2 py-1 bg-blue-500 text-white rounded text-xs"
            >
              保存
            </button>
            <button
              onClick={handleCancel}
              className="px-2 py-1 bg-gray-500 text-white rounded text-xs"
            >
              取消
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{annotation.text}</span>
            <div className="flex space-x-1">
              <button
                onClick={() => setIsEditing(true)}
                className="text-blue-500 hover:text-blue-700 text-xs"
              >
                编辑
              </button>
              <button
                onClick={onRemove}
                className="text-red-500 hover:text-red-700 text-xs"
              >
                删除
              </button>
            </div>
          </div>
          <div className="text-xs text-gray-500">
            {annotation.position.map((p, i) => 
              `${['X', 'Y', 'Z'][i]}: ${p.toFixed(2)}`
            ).join(', ')}
          </div>
        </div>
      )}
    </div>
  )
} 