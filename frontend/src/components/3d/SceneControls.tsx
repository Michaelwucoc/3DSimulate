import React, { useState } from 'react'
import { Button } from '../ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { 
  Settings, 
  Camera, 
  Lightbulb, 
  Ruler, 
  MessageSquare, 
  Download,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Move
} from 'lucide-react'

interface SceneControlsProps {
  onToggleStats?: () => void
  onToggleControls?: () => void
  onResetCamera?: () => void
  onExportModel?: () => void
  onToggleMeasurement?: () => void
  onToggleAnnotation?: () => void
}

export function SceneControls({
  onToggleStats,
  onToggleControls,
  onResetCamera,
  onExportModel,
  onToggleMeasurement,
  onToggleAnnotation
}: SceneControlsProps) {
  const [activeTab, setActiveTab] = useState<'camera' | 'lighting' | 'tools'>('camera')
  const [measurementMode, setMeasurementMode] = useState(false)
  const [annotationMode, setAnnotationMode] = useState(false)

  const handleMeasurementToggle = () => {
    setMeasurementMode(!measurementMode)
    onToggleMeasurement?.()
  }

  const handleAnnotationToggle = () => {
    setAnnotationMode(!annotationMode)
    onToggleAnnotation?.()
  }

  return (
    <div className="absolute top-4 right-4 z-10">
      <Card className="w-80 bg-white/90 backdrop-blur-sm border-white/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Settings className="w-5 h-5" />
            场景控制
          </CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* 标签页切换 */}
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('camera')}
              className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'camera' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Camera className="w-4 h-4 inline mr-1" />
              相机
            </button>
            <button
              onClick={() => setActiveTab('lighting')}
              className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'lighting' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Lightbulb className="w-4 h-4 inline mr-1" />
              光照
            </button>
            <button
              onClick={() => setActiveTab('tools')}
              className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'tools' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Settings className="w-4 h-4 inline mr-1" />
              工具
            </button>
          </div>

          {/* 相机控制 */}
          {activeTab === 'camera' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onResetCamera}
                  className="flex items-center gap-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  重置相机
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onToggleStats}
                  className="flex items-center gap-2"
                >
                  <Settings className="w-4 h-4" />
                  性能统计
                </Button>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">相机操作</label>
                <div className="grid grid-cols-3 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex flex-col items-center gap-1 p-2"
                  >
                    <Move className="w-4 h-4" />
                    <span className="text-xs">平移</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex flex-col items-center gap-1 p-2"
                  >
                    <RotateCcw className="w-4 h-4" />
                    <span className="text-xs">旋转</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex flex-col items-center gap-1 p-2"
                  >
                    <ZoomIn className="w-4 h-4" />
                    <span className="text-xs">缩放</span>
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* 光照控制 */}
          {activeTab === 'lighting' && (
            <div className="space-y-3">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">环境光强度</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  defaultValue="0.4"
                  className="w-full"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">方向光强度</label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  defaultValue="1"
                  className="w-full"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="shadows"
                  defaultChecked
                  className="rounded"
                />
                <label htmlFor="shadows" className="text-sm text-gray-700">
                  启用阴影
                </label>
              </div>
            </div>
          )}

          {/* 工具控制 */}
          {activeTab === 'tools' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant={measurementMode ? "default" : "outline"}
                  size="sm"
                  onClick={handleMeasurementToggle}
                  className="flex items-center gap-2"
                >
                  <Ruler className="w-4 h-4" />
                  测量工具
                </Button>
                <Button
                  variant={annotationMode ? "default" : "outline"}
                  size="sm"
                  onClick={handleAnnotationToggle}
                  className="flex items-center gap-2"
                >
                  <MessageSquare className="w-4 h-4" />
                  标注工具
                </Button>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={onExportModel}
                className="w-full flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                导出模型
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 