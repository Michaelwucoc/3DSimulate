import React, { useState, useCallback } from 'react'
import { Upload, Play, Settings, Info } from 'lucide-react'
import { Button } from './components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card'
import { Progress } from './components/ui/progress'
import { FileUpload } from './components/FileUpload'
import { Scene3D } from './components/3d/Scene3D'
import type { UploadFile, ReconstructionTask, ReconstructionResult } from './types'
import { generateId } from './lib/utils'
import { api } from './lib/api'

function App() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [currentTask, setCurrentTask] = useState<ReconstructionTask | null>(null)
  const [result, setResult] = useState<ReconstructionResult | null>(null)
  const [activeTab, setActiveTab] = useState<'upload' | 'process' | 'view'>('upload')
  const [reconstructionMethod, setReconstructionMethod] = useState<'nerf' | '3dgs'>('3dgs')

  // 处理文件上传
  const handleFilesChange = useCallback((uploadedFiles: UploadFile[]) => {
    setFiles(uploadedFiles)
  }, [])

  // 轮询任务状态
  const pollTaskStatus = useCallback(async (taskId: string) => {
    const poll = async () => {
      try {
        const response = await api.getTaskStatus(taskId)
        
        if (!response.success || !response.data) {
          throw new Error(response.error || '获取任务状态失败')
        }

        const { status, progress, message, result } = response.data
        
        setCurrentTask(prev => prev ? {
          ...prev,
          status,
          progress,
          message
        } : null)

        if (status === 'completed' && result) {
          setResult(result)
          setActiveTab('view')
          return // 停止轮询
        } else if (status === 'failed') {
          return // 停止轮询
        }
        
        // 继续轮询
        setTimeout(poll, 2000)
        
      } catch (error) {
        setCurrentTask(prev => prev ? {
          ...prev,
          status: 'failed',
          message: error instanceof Error ? error.message : '获取状态失败'
        } : null)
      }
    }
    
    poll()
  }, [])

  // 开始3D重建
  const startReconstruction = useCallback(async () => {
    if (files.length === 0) return

    const task: ReconstructionTask = {
      id: generateId(),
      status: 'processing',
      progress: 0,
      message: '正在上传文件...',
      files,
      createdAt: new Date(),
      method: reconstructionMethod
    }

    setCurrentTask(task)
    setActiveTab('process')

    try {
      // 上传文件
      const uploadResponse = await api.uploadFiles(files.map(f => f.file))
      
      if (!uploadResponse.success || !uploadResponse.data) {
        throw new Error(uploadResponse.error || '文件上传失败')
      }

      const taskId = uploadResponse.data.taskId
      
      // 更新任务ID
      const updatedTask = { ...task, id: taskId, message: '文件上传成功，开始重建...' }
      setCurrentTask(updatedTask)

      // 开始重建
      const startResponse = await api.startReconstruction(taskId, reconstructionMethod)
      
      if (!startResponse.success) {
        throw new Error(startResponse.error || '启动重建失败')
      }

      // 开始轮询任务状态
      pollTaskStatus(taskId)
      
    } catch (error) {
      setCurrentTask({
        ...task,
        status: 'failed',
        message: error instanceof Error ? error.message : '处理失败'
      })
    }
  }, [files, reconstructionMethod, pollTaskStatus])

  // 重新开始
  const restart = useCallback(() => {
    setFiles([])
    setCurrentTask(null)
    setResult(null)
    setActiveTab('upload')
  }, [])

  return (
    <div className="min-h-screen bg-white">
      {/* 头部 */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <span className="text-primary-foreground font-bold text-sm">3D</span>
                </div>
                <h1 className="text-xl font-bold">3D场景重建平台</h1>
              </div>
              
              {/* 导航标签 */}
              <nav className="flex space-x-1">
                <Button
                  variant={activeTab === 'upload' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveTab('upload')}
                  className="flex items-center space-x-2"
                >
                  <Upload className="h-4 w-4" />
                  <span>上传文件</span>
                </Button>
                <Button
                  variant={activeTab === 'process' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveTab('process')}
                  disabled={!currentTask}
                  className="flex items-center space-x-2"
                >
                  <Play className="h-4 w-4" />
                  <span>处理进度</span>
                </Button>
                <Button
                  variant={activeTab === 'view' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveTab('view')}
                  disabled={!result}
                  className="flex items-center space-x-2"
                >
                  <Info className="h-4 w-4" />
                  <span>3D查看器</span>
                </Button>
              </nav>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={restart}>
                重新开始
              </Button>
              <Button variant="ghost" size="icon">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="container mx-auto px-4 py-6">
        {activeTab === 'upload' && (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* 方法选择 */}
            <Card>
              <CardHeader>
                <CardTitle>选择重建方法</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex space-x-4">
                  <Button
                    variant={reconstructionMethod === '3dgs' ? 'default' : 'outline'}
                    onClick={() => setReconstructionMethod('3dgs')}
                    className="flex-1"
                  >
                    <div className="text-center">
                      <div className="font-semibold">3D Gaussian Splatting</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        快速重建，适合实时预览
                      </div>
                    </div>
                  </Button>
                  <Button
                    variant={reconstructionMethod === 'nerf' ? 'default' : 'outline'}
                    onClick={() => setReconstructionMethod('nerf')}
                    className="flex-1"
                  >
                    <div className="text-center">
                      <div className="font-semibold">Neural Radiance Fields</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        高质量重建，处理时间较长
                      </div>
                    </div>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* 文件上传 */}
            <Card>
              <CardHeader>
                <CardTitle>上传文件</CardTitle>
              </CardHeader>
              <CardContent>
                <FileUpload
                  onFilesChange={handleFilesChange}
                  maxFiles={20}
                  maxFileSize={500}
                />
              </CardContent>
            </Card>

            {/* 开始处理按钮 */}
            {files.length > 0 && (
              <div className="flex justify-center">
                <Button
                  onClick={startReconstruction}
                  size="lg"
                  className="px-8"
                >
                  开始3D重建
                </Button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'process' && currentTask && (
          <div className="max-w-2xl mx-auto space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>处理进度</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold mb-2">
                    {Math.round(currentTask.progress)}%
                  </div>
                  <Progress value={currentTask.progress} className="mb-4" />
                  <p className="text-muted-foreground">{currentTask.message}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-semibold">方法:</span> {currentTask.method.toUpperCase()}
                  </div>
                  <div>
                    <span className="font-semibold">文件数:</span> {currentTask.files.length}
                  </div>
                  <div>
                    <span className="font-semibold">开始时间:</span> {currentTask.createdAt.toLocaleTimeString()}
                  </div>
                  <div>
                    <span className="font-semibold">状态:</span> 
                    <span className={`ml-1 ${
                      currentTask.status === 'completed' ? 'text-green-600' :
                      currentTask.status === 'failed' ? 'text-red-600' :
                      'text-blue-600'
                    }`}>
                      {currentTask.status === 'completed' ? '已完成' :
                       currentTask.status === 'failed' ? '失败' : '处理中'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'view' && (
          <div className="h-[calc(100vh-200px)]">
            <Scene3D
              result={result || undefined}
              loading={currentTask?.status === 'processing'}
              error={currentTask?.status === 'failed' ? currentTask.message : undefined}
            />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
