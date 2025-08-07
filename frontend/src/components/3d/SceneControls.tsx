import React from 'react'
import { X, Sun, Grid3X3, Eye, Palette } from 'lucide-react'
import { Button } from '../ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Slider } from '../ui/slider'
import { Switch } from '../ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import type { SceneControls } from '../../types'

interface SceneControlsComponentProps {
  controls: SceneControls
  onChange: (controls: SceneControls) => void
  onClose: () => void
}

export function SceneControlsComponent({ controls, onChange, onClose }: SceneControlsComponentProps) {
  const updateControls = (updates: Partial<SceneControls>) => {
    onChange({ ...controls, ...updates })
  }

  const updateLighting = (updates: Partial<SceneControls['lighting']>) => {
    updateControls({
      lighting: { ...controls.lighting, ...updates }
    })
  }

  const updateRendering = (updates: Partial<SceneControls['rendering']>) => {
    updateControls({
      rendering: { ...controls.rendering, ...updates }
    })
  }

  const updateCamera = (updates: Partial<SceneControls['camera']>) => {
    updateControls({
      camera: { ...controls.camera, ...updates }
    })
  }

  return (
    <Card className="w-80 bg-white/95 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">场景设置</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* 照明设置 */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Sun className="h-4 w-4" />
            <span className="font-medium">照明</span>
          </div>
          
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <span className="text-sm">环境光强度</span>
              <span className="text-xs text-muted-foreground">{controls.lighting.ambient}</span>
            </div>
            <Slider
              value={[controls.lighting.ambient]}
              onValueChange={([value]) => updateLighting({ ambient: value })}
              min={0}
              max={2}
              step={0.1}
              className="w-full"
            />
            
            <div className="flex items-center justify-between">
              <span className="text-sm">主光源强度</span>
              <span className="text-xs text-muted-foreground">{controls.lighting.directional}</span>
            </div>
            <Slider
              value={[controls.lighting.directional]}
              onValueChange={([value]) => updateLighting({ directional: value })}
              min={0}
              max={3}
              step={0.1}
              className="w-full"
            />
            
            <div className="flex items-center justify-between">
              <span className="text-sm">阴影</span>
              <Switch
                checked={controls.lighting.shadows}
                onCheckedChange={(shadows) => updateLighting({ shadows })}
              />
            </div>
          </div>
        </div>

        {/* 渲染设置 */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Eye className="h-4 w-4" />
            <span className="font-medium">渲染</span>
          </div>
          
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <span className="text-sm">抗锯齿</span>
              <Switch
                checked={controls.rendering.antialiasing}
                onCheckedChange={(antialiasing) => updateRendering({ antialiasing })}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm">色调映射</span>
              <Switch
                checked={controls.rendering.toneMapping}
                onCheckedChange={(toneMapping) => updateRendering({ toneMapping })}
              />
            </div>
            
            <div className="space-y-2">
              <span className="text-sm">渲染质量</span>
              <Select
                value={controls.rendering.quality}
                onValueChange={(value) => updateRendering({ quality: value as 'low' | 'medium' | 'high' })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">低</SelectItem>
                  <SelectItem value="medium">中</SelectItem>
                  <SelectItem value="high">高</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* 相机设置 */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Palette className="h-4 w-4" />
            <span className="font-medium">相机</span>
          </div>
          
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <span className="text-sm">视野角度</span>
              <span className="text-xs text-muted-foreground">{controls.camera.fov}°</span>
            </div>
            <Slider
              value={[controls.camera.fov]}
              onValueChange={([value]) => updateCamera({ fov: value })}
              min={10}
              max={120}
              step={1}
              className="w-full"
            />
            
            <div className="flex items-center justify-between">
              <span className="text-sm">移动速度</span>
              <span className="text-xs text-muted-foreground">{controls.camera.speed}</span>
            </div>
            <Slider
              value={[controls.camera.speed]}
              onValueChange={([value]) => updateCamera({ speed: value })}
              min={0.1}
              max={2}
              step={0.1}
              className="w-full"
            />
          </div>
        </div>

        {/* 辅助显示 */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Grid3X3 className="h-4 w-4" />
            <span className="font-medium">辅助显示</span>
          </div>
          
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <span className="text-sm">网格</span>
              <Switch
                checked={controls.helpers.grid}
                onCheckedChange={(grid) => updateControls({
                  helpers: { ...controls.helpers, grid }
                })}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm">坐标轴</span>
              <Switch
                checked={controls.helpers.axes}
                onCheckedChange={(axes) => updateControls({
                  helpers: { ...controls.helpers, axes }
                })}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm">统计信息</span>
              <Switch
                checked={controls.helpers.stats}
                onCheckedChange={(stats) => updateControls({
                  helpers: { ...controls.helpers, stats }
                })}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}