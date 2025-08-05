import React, { useState } from 'react'
import { FileUpload } from './components/FileUpload'
import { Scene3D } from './components/3d/Scene3D'
import { useReconstruction } from './hooks/useReconstruction'
import { ReconstructionResult } from './types'
import { Button } from './components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card'
import { Progress } from './components/ui/progress'
import { 
  Upload, 
  Cube, 
  Settings, 
  Play, 
  Pause, 
  RotateCcw,
  Download,
  Eye,
  EyeOff
} from 'lucide-react'

function App() {
  const [currentView, setCurrentView] = useState<'upload' | 'reconstruction' | 'viewer'>('upload')
  const [currentModel, setCurrentModel] = useState<ReconstructionResult | null>(null)
  const [showControls, setShowControls] = useState(true)

  const {
    tasks,
    currentTask,
    isPolling,
    error,
    createTask,
    startPolling,
    stopPolling,
    deleteTask,
    restartTask
  } = useReconstruction({ autoStart: true })

  const handleUploadComplete = (fileIds: string[]) => {
    console.log('Files uploaded:', fileIds)
    // 这里可以显示上传成功的消息
  }

  const handleStartReconstruction = async (fileIds: string[]) => {
    console.log('Starting reconstruction with files:', fileIds)
    setCurrentView('reconstruction')
    
    const taskId = await createTask(fileIds)
    if (taskId) {
      startPolling(taskId)
    }
  }

  const handleReconstructionComplete = (result: ReconstructionResult) => {
    setCurrentModel(result)
    setCurrentView('viewer')
  }

  const handleExportModel = () => {
    if (currentModel) {
      // 创建下载链接
      const link = document.createElement('a')
      link.href = currentModel.modelUrl
      link.download = `3d-model-${currentModel.id}.glb`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const handleResetCamera = () => {
    // 重置相机位置的逻辑
    console.log('Resetting camera')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Cube className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">3D场景重建平台</h1>
            </div>
            
            <nav className="flex space-x-4">
              <Button
                variant={currentView === 'upload' ? 'default' : 'ghost'}
                onClick={() => setCurrentView('upload')}
                className="flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                上传文件
              </Button>
              <Button
                variant={currentView === 'reconstruction' ? 'default' : 'ghost'}
                onClick={() => setCurrentView('reconstruction')}
                className="flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                重建任务
              </Button>
              <Button
                variant={currentView === 'viewer' ? 'default' : 'ghost'}
                onClick={() => setCurrentView('viewer')}
                className="flex items-center gap-2"
                disabled={!currentModel}
              >
                <Eye className="w-4 h-4" />
                3D查看器
              </Button>
            </nav>
          </div>
        </div>
      </header>

      {/* 主要内容区域 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'upload' && (
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                上传文件进行3D重建
              </h2>
              <p className="text-gray-600">
                上传视频文件或图片，我们将使用先进的NeRF和3D Gaussian Splatting技术为您生成高质量的3D场景。
              </p>
            </div>
            
            <FileUpload
              onUploadComplete={handleUploadComplete}
              onStartReconstruction={handleStartReconstruction}
            />
          </div>
        )}

        {currentView === 'reconstruction' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">重建任务</h2>
              <Button
                variant="outline"
                onClick={() => setCurrentView('upload')}
                className="flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                上传新文件
              </Button>
            </div>

            {/* 当前任务状态 */}
            {currentTask && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="w-5 h-5" />
                    当前任务: {currentTask.id}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">状态: {currentTask.status}</span>
                      <span className="text-sm text-gray-500">
                        {currentTask.createdAt.toLocaleString()}
                      </span>
                    </div>
                    
                    <Progress value={currentTask.progress} className="w-full" />
                    
                    <p className="text-sm text-gray-600">{currentTask.message}</p>
                    
                    <div className="flex gap-2">
                      {currentTask.status === 'processing' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => stopPolling()}
                        >
                          <Pause className="w-4 h-4 mr-2" />
                          暂停
                        </Button>
                      )}
                      
                      {currentTask.status === 'failed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => restartTask(currentTask.id)}
                        >
                          <RotateCcw className="w-4 h-4 mr-2" />
                          重试
                        </Button>
                      )}
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => deleteTask(currentTask.id)}
                      >
                        删除任务
                      </Button>
                    </div>

                    {/* 重建完成时显示结果 */}
                    {currentTask.status === 'completed' && currentTask.result && (
                      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="font-medium text-green-800">重建完成!</span>
                        </div>
                        <p className="text-sm text-green-700 mb-3">
                          处理时间: {currentTask.result.statistics.processingTime}s
                        </p>
                        <Button
                          onClick={() => handleReconstructionComplete(currentTask.result!)}
                          className="flex items-center gap-2"
                        >
                          <Eye className="w-4 h-4" />
                          查看3D模型
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 任务列表 */}
            {tasks.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>历史任务</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {tasks.map(task => (
                      <div
                        key={task.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-sm">{task.id}</p>
                          <p className="text-xs text-gray-500">
                            {task.status} • {task.createdAt.toLocaleString()}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => deleteTask(task.id)}
                          >
                            删除
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="pt-6">
                  <p className="text-red-600">{error}</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {currentView === 'viewer' && currentModel && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">3D场景查看器</h2>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setShowControls(!showControls)}
                  className="flex items-center gap-2"
                >
                  {showControls ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  {showControls ? '隐藏控制' : '显示控制'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleResetCamera}
                  className="flex items-center gap-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  重置相机
                </Button>
                <Button
                  onClick={handleExportModel}
                  className="flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  导出模型
                </Button>
              </div>
            </div>

            {/* 3D场景容器 */}
            <div className="h-[600px] rounded-lg overflow-hidden shadow-lg">
              <Scene3D
                modelData={currentModel}
                onSceneReady={() => console.log('3D scene ready')}
              />
            </div>

            {/* 模型信息 */}
            <Card>
              <CardHeader>
                <CardTitle>模型信息</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">顶点数</p>
                    <p className="text-lg font-semibold">{currentModel.metadata.vertices.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">面数</p>
                    <p className="text-lg font-semibold">{currentModel.metadata.faces.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">处理时间</p>
                    <p className="text-lg font-semibold">{currentModel.statistics.processingTime}s</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">质量</p>
                    <p className="text-lg font-semibold capitalize">{currentModel.statistics.quality}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
