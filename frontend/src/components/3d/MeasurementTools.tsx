import React, { useState } from 'react'
import { X, Ruler, Triangle, Square, Box, Trash2, Eye, EyeOff } from 'lucide-react'
import { Button } from '../ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import type { Measurement } from '../../types'
import { generateId } from '../../lib/utils'

interface MeasurementToolsProps {
  onClose: () => void
}

export function MeasurementTools({ onClose }: MeasurementToolsProps) {
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [selectedTool, setSelectedTool] = useState<Measurement['type']>('distance')
  const [isActive, setIsActive] = useState(false)

  const addMeasurement = (type: Measurement['type']) => {
    const newMeasurement: Measurement = {
      id: generateId(),
      type,
      points: [],
      value: 0,
      unit: type === 'distance' ? 'm' : type === 'angle' ? '°' : type === 'area' ? 'm²' : 'm³',
      color: '#ff6b6b',
      visible: true
    }
    setMeasurements(prev => [...prev, newMeasurement])
  }

  const deleteMeasurement = (id: string) => {
    setMeasurements(prev => prev.filter(m => m.id !== id))
  }

  const toggleMeasurementVisibility = (id: string) => {
    setMeasurements(prev => prev.map(m => 
      m.id === id ? { ...m, visible: !m.visible } : m
    ))
  }

  const clearAllMeasurements = () => {
    setMeasurements([])
  }

  const getToolIcon = (type: Measurement['type']) => {
    switch (type) {
      case 'distance': return <Ruler className="h-4 w-4" />
      case 'angle': return <Triangle className="h-4 w-4" />
      case 'area': return <Square className="h-4 w-4" />
      case 'volume': return <Box className="h-4 w-4" />
      default: return <Ruler className="h-4 w-4" />
    }
  }

  const getToolName = (type: Measurement['type']) => {
    switch (type) {
      case 'distance': return '距离测量'
      case 'angle': return '角度测量'
      case 'area': return '面积测量'
      case 'volume': return '体积测量'
      default: return '测量'
    }
  }

  return (
    <Card className="w-80 bg-white/95 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">测量工具</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 工具选择 */}
        <div className="space-y-2">
          <label className="text-sm font-medium">测量类型</label>
          <Select value={selectedTool} onValueChange={(value) => setSelectedTool(value as Measurement['type'])}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="distance">距离测量</SelectItem>
              <SelectItem value="angle">角度测量</SelectItem>
              <SelectItem value="area">面积测量</SelectItem>
              <SelectItem value="volume">体积测量</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 操作按钮 */}
        <div className="flex space-x-2">
          <Button
            variant={isActive ? "default" : "outline"}
            onClick={() => {
              setIsActive(!isActive)
              if (!isActive) {
                addMeasurement(selectedTool)
              }
            }}
            className="flex-1"
          >
            {getToolIcon(selectedTool)}
            <span className="ml-2">
              {isActive ? '停止测量' : '开始测量'}
            </span>
          </Button>
          
          {measurements.length > 0 && (
            <Button
              variant="outline"
              size="icon"
              onClick={clearAllMeasurements}
              title="清除所有测量"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* 测量说明 */}
        {isActive && (
          <div className="p-3 bg-muted rounded-lg">
            <div className="text-sm text-muted-foreground">
              {selectedTool === 'distance' && '点击两个点来测量距离'}
              {selectedTool === 'angle' && '点击三个点来测量角度'}
              {selectedTool === 'area' && '点击多个点来测量面积'}
              {selectedTool === 'volume' && '选择一个区域来测量体积'}
            </div>
          </div>
        )}

        {/* 测量结果列表 */}
        {measurements.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">测量结果</span>
              <span className="text-xs text-muted-foreground">{measurements.length} 项</span>
            </div>
            
            <div className="max-h-48 overflow-y-auto space-y-2">
              {measurements.map((measurement) => (
                <div
                  key={measurement.id}
                  className="flex items-center justify-between p-2 bg-muted rounded-lg"
                >
                  <div className="flex items-center space-x-2">
                    {getToolIcon(measurement.type)}
                    <div>
                      <div className="text-sm font-medium">
                        {getToolName(measurement.type)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {measurement.value.toFixed(2)} {measurement.unit}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => toggleMeasurementVisibility(measurement.id)}
                      className="h-6 w-6"
                    >
                      {measurement.visible ? (
                        <Eye className="h-3 w-3" />
                      ) : (
                        <EyeOff className="h-3 w-3" />
                      )}
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteMeasurement(measurement.id)}
                      className="h-6 w-6 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 空状态 */}
        {measurements.length === 0 && !isActive && (
          <div className="text-center py-8 text-muted-foreground">
            <Ruler className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <div className="text-sm">暂无测量数据</div>
            <div className="text-xs">选择测量类型并开始测量</div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}