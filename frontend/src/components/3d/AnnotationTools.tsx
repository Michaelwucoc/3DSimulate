import React, { useState } from 'react'
import { X, MessageSquare, MapPin, ArrowRight, Trash2, Eye, EyeOff } from 'lucide-react'
import { Button } from '../ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import type { Annotation } from '../../types'
import { generateId } from '../../lib/utils'

interface AnnotationToolsProps {
  onClose: () => void
}

const ANNOTATION_COLORS = [
  '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
  '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43'
]

export function AnnotationTools({ onClose }: AnnotationToolsProps) {
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [selectedType, setSelectedType] = useState<Annotation['type']>('point')
  const [selectedColor, setSelectedColor] = useState(ANNOTATION_COLORS[0])
  const [isActive, setIsActive] = useState(false)
  const [newAnnotationText, setNewAnnotationText] = useState('')

  const addAnnotation = (type: Annotation['type']) => {
    const newAnnotation: Annotation = {
      id: generateId(),
      position: [0, 0, 0], // 将在3D场景中设置实际位置
      text: newAnnotationText || `${getTypeName(type)} ${annotations.length + 1}`,
      color: selectedColor,
      visible: true,
      type,
      size: 1.0
    }
    setAnnotations(prev => [...prev, newAnnotation])
    setNewAnnotationText('')
  }

  const deleteAnnotation = (id: string) => {
    setAnnotations(prev => prev.filter(a => a.id !== id))
  }

  const toggleAnnotationVisibility = (id: string) => {
    setAnnotations(prev => prev.map(a => 
      a.id === id ? { ...a, visible: !a.visible } : a
    ))
  }

  const updateAnnotationText = (id: string, text: string) => {
    setAnnotations(prev => prev.map(a => 
      a.id === id ? { ...a, text } : a
    ))
  }

  const clearAllAnnotations = () => {
    setAnnotations([])
  }

  const getTypeIcon = (type: Annotation['type']) => {
    switch (type) {
      case 'point': return <MapPin className="h-4 w-4" />
      case 'text': return <MessageSquare className="h-4 w-4" />
      case 'arrow': return <ArrowRight className="h-4 w-4" />
      default: return <MapPin className="h-4 w-4" />
    }
  }

  const getTypeName = (type: Annotation['type']) => {
    switch (type) {
      case 'point': return '点标注'
      case 'text': return '文本标注'
      case 'arrow': return '箭头标注'
      default: return '标注'
    }
  }

  return (
    <Card className="w-80 bg-white/95 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">标注工具</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 标注类型选择 */}
        <div className="space-y-2">
          <label className="text-sm font-medium">标注类型</label>
          <Select value={selectedType} onValueChange={(value) => setSelectedType(value as Annotation['type'])}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="point">点标注</SelectItem>
              <SelectItem value="text">文本标注</SelectItem>
              <SelectItem value="arrow">箭头标注</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 颜色选择 */}
        <div className="space-y-2">
          <label className="text-sm font-medium">颜色</label>
          <div className="flex flex-wrap gap-2">
            {ANNOTATION_COLORS.map((color) => (
              <button
                key={color}
                onClick={() => setSelectedColor(color)}
                className={`w-6 h-6 rounded-full border-2 transition-all ${
                  selectedColor === color ? 'border-foreground scale-110' : 'border-muted'
                }`}
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>
        </div>

        {/* 标注文本输入 */}
        <div className="space-y-2">
          <label className="text-sm font-medium">标注文本</label>
          <input
            type="text"
            value={newAnnotationText}
            onChange={(e) => setNewAnnotationText(e.target.value)}
            placeholder={`输入${getTypeName(selectedType)}文本...`}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          />
        </div>

        {/* 操作按钮 */}
        <div className="flex space-x-2">
          <Button
            variant={isActive ? "default" : "outline"}
            onClick={() => {
              setIsActive(!isActive)
              if (!isActive) {
                addAnnotation(selectedType)
              }
            }}
            className="flex-1"
          >
            {getTypeIcon(selectedType)}
            <span className="ml-2">
              {isActive ? '停止标注' : '开始标注'}
            </span>
          </Button>
          
          {annotations.length > 0 && (
            <Button
              variant="outline"
              size="icon"
              onClick={clearAllAnnotations}
              title="清除所有标注"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* 标注说明 */}
        {isActive && (
          <div className="p-3 bg-muted rounded-lg">
            <div className="text-sm text-muted-foreground">
              {selectedType === 'point' && '点击3D场景中的位置添加点标注'}
              {selectedType === 'text' && '点击3D场景中的位置添加文本标注'}
              {selectedType === 'arrow' && '点击起点和终点添加箭头标注'}
            </div>
          </div>
        )}

        {/* 标注列表 */}
        {annotations.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">标注列表</span>
              <span className="text-xs text-muted-foreground">{annotations.length} 项</span>
            </div>
            
            <div className="max-h-48 overflow-y-auto space-y-2">
              {annotations.map((annotation) => (
                <div
                  key={annotation.id}
                  className="p-2 bg-muted rounded-lg space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getTypeIcon(annotation.type)}
                      <div
                        className="w-3 h-3 rounded-full border"
                        style={{ backgroundColor: annotation.color }}
                      />
                      <span className="text-sm font-medium">
                        {getTypeName(annotation.type)}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => toggleAnnotationVisibility(annotation.id)}
                        className="h-6 w-6"
                      >
                        {annotation.visible ? (
                          <Eye className="h-3 w-3" />
                        ) : (
                          <EyeOff className="h-3 w-3" />
                        )}
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteAnnotation(annotation.id)}
                        className="h-6 w-6 text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  
                  <input
                    type="text"
                    value={annotation.text}
                    onChange={(e) => updateAnnotationText(annotation.id, e.target.value)}
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="标注文本..."
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 空状态 */}
        {annotations.length === 0 && !isActive && (
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <div className="text-sm">暂无标注</div>
            <div className="text-xs">选择标注类型并开始标注</div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}