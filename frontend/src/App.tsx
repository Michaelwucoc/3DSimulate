import React, { useState, useCallback } from 'react'
import './App.css'
import { Upload, Play, Settings, Sparkles, Zap, Eye, Cpu, Layers, Camera } from 'lucide-react'
import { Button } from './components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card'
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

      const taskId = uploadResponse.data.task_id
      
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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 via-purple-950 to-slate-950 relative overflow-hidden">
      {/* 增强的动态背景系统 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* 多层网格效果 */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:100px_100px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)] animate-pulse"></div>
        <div className="absolute inset-0 bg-[linear-gradient(rgba(168,85,247,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(168,85,247,0.02)_1px,transparent_1px)] bg-[size:50px_50px] [mask-image:radial-gradient(ellipse_60%_40%_at_50%_50%,#000_60%,transparent_100%)]"></div>
        
        {/* 增强的浮动粒子系统 */}
        <div className="absolute top-20 left-20 w-3 h-3 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full animate-ping shadow-lg shadow-cyan-400/50" style={{animationDelay: '0s'}}></div>
        <div className="absolute top-40 right-32 w-2 h-2 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full animate-ping shadow-lg shadow-purple-400/50" style={{animationDelay: '1s'}}></div>
        <div className="absolute bottom-32 left-40 w-2.5 h-2.5 bg-gradient-to-r from-pink-400 to-rose-500 rounded-full animate-ping shadow-lg shadow-pink-400/50" style={{animationDelay: '2s'}}></div>
        <div className="absolute bottom-20 right-20 w-2 h-2 bg-gradient-to-r from-cyan-400 to-teal-500 rounded-full animate-ping shadow-lg shadow-cyan-400/50" style={{animationDelay: '3s'}}></div>
        <div className="absolute top-1/4 left-1/4 w-1.5 h-1.5 bg-gradient-to-r from-emerald-400 to-green-500 rounded-full animate-ping shadow-lg shadow-emerald-400/50" style={{animationDelay: '4s'}}></div>
        <div className="absolute top-3/4 right-1/4 w-2 h-2 bg-gradient-to-r from-violet-400 to-purple-500 rounded-full animate-ping shadow-lg shadow-violet-400/50" style={{animationDelay: '5s'}}></div>
        
        {/* 多层次光晕效果 */}
        <div className="absolute -top-60 -right-60 w-[500px] h-[500px] bg-gradient-to-br from-blue-500/15 via-cyan-500/10 via-purple-500/15 to-transparent rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-60 -left-60 w-[500px] h-[500px] bg-gradient-to-br from-purple-500/15 via-pink-500/10 via-indigo-500/15 to-transparent rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-gradient-to-br from-cyan-500/8 via-blue-500/8 via-teal-500/8 to-transparent rounded-full blur-3xl animate-pulse" style={{animationDelay: '4s'}}></div>
        <div className="absolute top-2/3 right-1/3 w-80 h-80 bg-gradient-to-br from-violet-500/8 via-purple-500/8 via-fuchsia-500/8 to-transparent rounded-full blur-3xl animate-pulse" style={{animationDelay: '6s'}}></div>
        
        {/* 动态射线效果 */}
        <div className="absolute top-0 left-1/2 w-px h-full bg-gradient-to-b from-transparent via-cyan-400/20 to-transparent animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-purple-400/20 to-transparent animate-pulse" style={{animationDelay: '3s'}}></div>
      </div>
      
      {/* 增强的头部导航 */}
      <header className="relative z-10 border-b border-white/10 bg-gradient-to-r from-black/30 via-slate-900/40 to-black/30 backdrop-blur-3xl shadow-2xl">
        {/* 头部装饰线 */}
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400/50 via-purple-400/50 to-transparent"></div>
        <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-blue-400/30 via-pink-400/30 to-transparent"></div>
        
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-10">
              <div className="flex items-center space-x-5">
                <div className="relative group">
                  {/* 多层光晕效果 */}
                  <div className="absolute -inset-3 bg-gradient-to-r from-cyan-400/20 via-blue-500/20 to-purple-600/20 rounded-3xl blur-xl animate-pulse"></div>
                  <div className="absolute -inset-2 bg-gradient-to-r from-cyan-400/30 via-blue-500/30 to-purple-600/30 rounded-3xl blur-lg animate-pulse" style={{animationDelay: '0.5s'}}></div>
                  
                  <div className="relative w-16 h-16 bg-gradient-to-br from-cyan-400 via-blue-500 via-purple-600 to-pink-500 rounded-3xl flex items-center justify-center shadow-2xl group-hover:scale-110 transition-all duration-500">
                    <div className="w-8 h-8 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                      <Layers className="h-5 w-5 text-white" />
                    </div>
                  </div>
                  
                  {/* 状态指示器 */}
                  <div className="absolute -top-1 -right-1 w-5 h-5 bg-gradient-to-br from-emerald-400 to-green-500 rounded-full animate-pulse shadow-lg shadow-emerald-400/50 flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                </div>
                <div className="space-y-1">
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-cyan-200 via-blue-200 to-purple-200 bg-clip-text text-transparent tracking-tight">
                    NeuroVision 3D
                  </h1>
                  <p className="text-sm text-gray-300 font-medium tracking-wide flex items-center space-x-2">
                    <span className="w-2 h-2 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full animate-pulse"></span>
                    <span>AI-Powered Scene Reconstruction</span>
                  </p>
                </div>
              </div>
              
              {/* 导航标签 */}
              <nav className="flex space-x-2 bg-gradient-to-r from-black/40 via-slate-900/50 to-black/40 backdrop-blur-xl rounded-3xl p-2 border border-white/20 shadow-2xl">
                <Button
                  variant={activeTab === 'upload' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveTab('upload')}
                  className={`relative flex items-center space-x-3 rounded-2xl px-6 py-3.5 transition-all duration-500 overflow-hidden group ${
                    activeTab === 'upload' 
                      ? 'bg-gradient-to-r from-cyan-500/30 via-blue-500/30 to-cyan-600/30 text-white shadow-2xl shadow-cyan-500/40 scale-105 border border-cyan-400/50' 
                      : 'hover:bg-gradient-to-r hover:from-white/10 hover:to-white/5 text-gray-300 hover:text-white hover:scale-102'
                  }`}
                >
                  {/* 背景光效 */}
                  <div className={`absolute inset-0 bg-gradient-to-r transition-all duration-500 ${
                    activeTab === 'upload' 
                      ? 'from-cyan-400/20 via-blue-500/20 to-cyan-500/20 opacity-100' 
                      : 'from-cyan-500/0 to-blue-500/0 opacity-0 group-hover:opacity-100 group-hover:from-cyan-500/10 group-hover:to-blue-500/10'
                  }`}></div>
                  
                  <div className="relative z-10 flex items-center space-x-3">
                    <div className={`p-1.5 rounded-lg transition-all duration-300 ${
                      activeTab === 'upload'
                        ? 'bg-white/20 shadow-lg'
                        : 'group-hover:bg-white/10'
                    }`}>
                      <Upload className="h-4 w-4" />
                    </div>
                    <span className="font-semibold tracking-wide">上传</span>
                  </div>
                  
                  {/* 活跃状态指示器 */}
                  {activeTab === 'upload' && (
                    <>
                      <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-500 rounded-full"></div>
                      <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full blur-sm animate-pulse"></div>
                    </>
                  )}
                  
                  {/* 悬浮粒子效果 */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                    <div className="absolute top-2 left-4 w-1 h-1 bg-cyan-400 rounded-full animate-ping" style={{animationDelay: '0s'}}></div>
                    <div className="absolute bottom-2 right-4 w-1 h-1 bg-blue-400 rounded-full animate-ping" style={{animationDelay: '0.5s'}}></div>
                  </div>
                </Button>
                
                <Button
                  variant={activeTab === 'process' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveTab('process')}
                  disabled={!currentTask}
                  className={`relative flex items-center space-x-3 rounded-2xl px-6 py-3.5 transition-all duration-500 overflow-hidden group ${
                    activeTab === 'process' 
                      ? 'bg-gradient-to-r from-purple-500/30 via-pink-500/30 to-purple-600/30 text-white shadow-2xl shadow-purple-500/40 scale-105 border border-purple-400/50' 
                      : 'hover:bg-gradient-to-r hover:from-white/10 hover:to-white/5 text-gray-300 hover:text-white hover:scale-102 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100'
                  }`}
                >
                  {/* 背景光效 */}
                  <div className={`absolute inset-0 bg-gradient-to-r transition-all duration-500 ${
                    activeTab === 'process' 
                      ? 'from-purple-400/20 via-pink-500/20 to-purple-500/20 opacity-100' 
                      : 'from-purple-500/0 to-pink-500/0 opacity-0 group-hover:opacity-100 group-hover:from-purple-500/10 group-hover:to-pink-500/10'
                  }`}></div>
                  
                  <div className="relative z-10 flex items-center space-x-3">
                    <div className={`p-1.5 rounded-lg transition-all duration-300 ${
                      activeTab === 'process'
                        ? 'bg-white/20 shadow-lg'
                        : 'group-hover:bg-white/10'
                    }`}>
                      <Cpu className="h-4 w-4" />
                    </div>
                    <span className="font-semibold tracking-wide">处理</span>
                  </div>
                  
                  {/* 活跃状态指示器 */}
                  {activeTab === 'process' && (
                    <>
                      <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-purple-400 via-pink-500 to-purple-500 rounded-full"></div>
                      <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full blur-sm animate-pulse"></div>
                    </>
                  )}
                  
                  {/* 悬浮粒子效果 */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                    <div className="absolute top-2 left-4 w-1 h-1 bg-purple-400 rounded-full animate-ping" style={{animationDelay: '0s'}}></div>
                    <div className="absolute bottom-2 right-4 w-1 h-1 bg-pink-400 rounded-full animate-ping" style={{animationDelay: '0.5s'}}></div>
                  </div>
                </Button>
                
                <Button
                  variant={activeTab === 'view' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveTab('view')}
                  disabled={!result}
                  className={`relative flex items-center space-x-3 rounded-2xl px-6 py-3.5 transition-all duration-500 overflow-hidden group ${
                    activeTab === 'view' 
                      ? 'bg-gradient-to-r from-emerald-500/30 via-teal-500/30 to-emerald-600/30 text-white shadow-2xl shadow-emerald-500/40 scale-105 border border-emerald-400/50' 
                      : 'hover:bg-gradient-to-r hover:from-white/10 hover:to-white/5 text-gray-300 hover:text-white hover:scale-102 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100'
                  }`}
                >
                  {/* 背景光效 */}
                  <div className={`absolute inset-0 bg-gradient-to-r transition-all duration-500 ${
                    activeTab === 'view' 
                      ? 'from-emerald-400/20 via-teal-500/20 to-emerald-500/20 opacity-100' 
                      : 'from-emerald-500/0 to-teal-500/0 opacity-0 group-hover:opacity-100 group-hover:from-emerald-500/10 group-hover:to-teal-500/10'
                  }`}></div>
                  
                  <div className="relative z-10 flex items-center space-x-3">
                    <div className={`p-1.5 rounded-lg transition-all duration-300 ${
                      activeTab === 'view'
                        ? 'bg-white/20 shadow-lg'
                        : 'group-hover:bg-white/10'
                    }`}>
                      <Eye className="h-4 w-4" />
                    </div>
                    <span className="font-semibold tracking-wide">查看</span>
                  </div>
                  
                  {/* 活跃状态指示器 */}
                  {activeTab === 'view' && (
                    <>
                      <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 via-teal-500 to-emerald-500 rounded-full"></div>
                      <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full blur-sm animate-pulse"></div>
                    </>
                  )}
                  
                  {/* 悬浮粒子效果 */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                    <div className="absolute top-2 left-4 w-1 h-1 bg-emerald-400 rounded-full animate-ping" style={{animationDelay: '0s'}}></div>
                    <div className="absolute bottom-2 right-4 w-1 h-1 bg-teal-400 rounded-full animate-ping" style={{animationDelay: '0.5s'}}></div>
                  </div>
                </Button>
              </nav>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={restart}
                className="bg-white/5 backdrop-blur-sm border-white/20 hover:bg-white/10 hover:border-white/30 text-gray-300 hover:text-white shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl px-4 py-2"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                重新开始
              </Button>
              <Button 
                variant="ghost" 
                size="icon"
                className="bg-white/5 backdrop-blur-sm hover:bg-white/10 text-gray-400 hover:text-white rounded-xl transition-all duration-300 w-10 h-10"
              >
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        {activeTab === 'upload' && (
          <div className="max-w-6xl mx-auto space-y-8">
            {/* 方法选择 */}
            <Card className="border-0 shadow-2xl bg-black/40 backdrop-blur-2xl relative overflow-hidden border border-white/10">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-purple-500/5"></div>
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600"></div>
              
              {/* 装饰性几何图形 */}
              <div className="absolute top-4 right-4 w-20 h-20 border border-cyan-400/20 rounded-full animate-spin" style={{animationDuration: '20s'}}></div>
              <div className="absolute bottom-4 left-4 w-16 h-16 border border-purple-400/20 rounded-lg rotate-45 animate-pulse"></div>
              
              <CardHeader className="relative text-center pb-8">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-cyan-500 via-blue-600 to-purple-700 rounded-3xl shadow-2xl mb-6 mx-auto relative">
                  <Zap className="h-10 w-10 text-white" />
                  <div className="absolute -inset-1 bg-gradient-to-r from-cyan-400 to-purple-600 rounded-3xl blur opacity-30 animate-pulse"></div>
                </div>
                <CardTitle className="text-4xl font-bold bg-gradient-to-r from-white via-cyan-200 to-blue-200 bg-clip-text text-transparent mb-4">
                  选择重建算法
                </CardTitle>
                <p className="text-gray-300 text-lg leading-relaxed max-w-2xl mx-auto">选择最适合您项目的3D重建技术，体验下一代神经渲染的强大能力</p>
              </CardHeader>
              <CardContent className="relative">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                  <div
                    onClick={() => setReconstructionMethod('3dgs')}
                    className={`group relative p-10 rounded-3xl border cursor-pointer transition-all duration-700 hover:scale-[1.03] hover:-translate-y-3 ${
                      reconstructionMethod === '3dgs'
                        ? 'border-cyan-400/50 bg-gradient-to-br from-cyan-500/10 via-blue-500/10 to-transparent shadow-2xl shadow-cyan-500/20'
                        : 'border-white/20 bg-black/20 backdrop-blur-sm hover:border-cyan-400/30 hover:shadow-2xl hover:shadow-cyan-500/10 hover:bg-gradient-to-br hover:from-cyan-500/5 hover:to-transparent'
                    }`}
                  >
                    {/* 选中指示器 */}
                    {reconstructionMethod === '3dgs' && (
                      <div className="absolute -top-4 -right-4 w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-full flex items-center justify-center shadow-2xl animate-pulse">
                        <div className="w-4 h-4 bg-white rounded-full"></div>
                      </div>
                    )}
                    
                    {/* 背景装饰 */}
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-cyan-500/10 via-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                    <div className="absolute top-4 right-4 w-32 h-32 border border-cyan-400/10 rounded-full animate-spin" style={{animationDuration: '15s'}}></div>
                    
                    <div className="relative text-center space-y-8">
                      <div className="w-24 h-24 mx-auto bg-gradient-to-br from-cyan-400 via-blue-500 to-blue-700 rounded-3xl flex items-center justify-center shadow-2xl group-hover:shadow-cyan-500/50 transition-all duration-500 group-hover:scale-110 relative">
                        <Zap className="h-12 w-12 text-white" />
                        <div className="absolute -inset-1 bg-gradient-to-r from-cyan-400 to-blue-600 rounded-3xl blur opacity-30 group-hover:opacity-60 transition-opacity duration-500"></div>
                      </div>
                      <div>
                        <h3 className="font-bold text-2xl text-white mb-4 group-hover:text-cyan-300 transition-colors duration-500">3D Gaussian Splatting</h3>
                        <p className="text-gray-300 leading-relaxed text-lg group-hover:text-gray-200 transition-colors duration-500">
                          革命性的实时渲染技术，提供极速重建和流畅交互体验
                        </p>
                      </div>
                      <div className="flex items-center justify-center space-x-4">
                        <div className="flex items-center space-x-2 px-4 py-2 bg-emerald-500/20 border border-emerald-400/30 rounded-full backdrop-blur-sm">
                          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                          <span className="text-emerald-300 font-semibold text-sm">极速处理</span>
                        </div>
                        <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 border border-blue-400/30 rounded-full backdrop-blur-sm">
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                          <span className="text-blue-300 font-semibold text-sm">实时渲染</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => setReconstructionMethod('nerf')}
                    className={`group relative p-10 rounded-3xl border cursor-pointer transition-all duration-700 hover:scale-[1.03] hover:-translate-y-3 ${
                      reconstructionMethod === 'nerf'
                        ? 'border-purple-400/50 bg-gradient-to-br from-purple-500/10 via-pink-500/10 to-transparent shadow-2xl shadow-purple-500/20'
                        : 'border-white/20 bg-black/20 backdrop-blur-sm hover:border-purple-400/30 hover:shadow-2xl hover:shadow-purple-500/10 hover:bg-gradient-to-br hover:from-purple-500/5 hover:to-transparent'
                    }`}
                  >
                    {/* 选中指示器 */}
                    {reconstructionMethod === 'nerf' && (
                      <div className="absolute -top-4 -right-4 w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full flex items-center justify-center shadow-2xl animate-pulse">
                        <div className="w-4 h-4 bg-white rounded-full"></div>
                      </div>
                    )}
                    
                    {/* 背景装饰 */}
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-purple-500/10 via-pink-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                    <div className="absolute top-4 left-4 w-28 h-28 border border-purple-400/10 rounded-lg rotate-12 animate-pulse"></div>
                    
                    <div className="relative text-center space-y-8">
                      <div className="w-24 h-24 mx-auto bg-gradient-to-br from-purple-400 via-purple-600 to-pink-700 rounded-3xl flex items-center justify-center shadow-2xl group-hover:shadow-purple-500/50 transition-all duration-500 group-hover:scale-110 relative">
                        <Camera className="h-12 w-12 text-white" />
                        <div className="absolute -inset-1 bg-gradient-to-r from-purple-400 to-pink-600 rounded-3xl blur opacity-30 group-hover:opacity-60 transition-opacity duration-500"></div>
                      </div>
                      <div>
                        <h3 className="font-bold text-2xl text-white mb-4 group-hover:text-purple-300 transition-colors duration-500">Neural Radiance Fields</h3>
                        <p className="text-gray-300 leading-relaxed text-lg group-hover:text-gray-200 transition-colors duration-500">
                          前沿神经网络技术，生成电影级逼真3D场景和光照效果
                        </p>
                      </div>
                      <div className="flex items-center justify-center space-x-4">
                        <div className="flex items-center space-x-2 px-4 py-2 bg-purple-500/20 border border-purple-400/30 rounded-full backdrop-blur-sm">
                          <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
                          <span className="text-purple-300 font-semibold text-sm">超高质量</span>
                        </div>
                        <div className="flex items-center space-x-2 px-4 py-2 bg-pink-500/20 border border-pink-400/30 rounded-full backdrop-blur-sm">
                          <div className="w-2 h-2 bg-pink-400 rounded-full animate-pulse"></div>
                          <span className="text-pink-300 font-semibold text-sm">逼真光影</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 文件上传 */}
            <Card className="border-0 shadow-2xl bg-black/40 backdrop-blur-2xl relative overflow-hidden border border-white/10">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-teal-500/5"></div>
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 via-teal-500 to-cyan-600"></div>
              
              {/* 装饰性元素 */}
              <div className="absolute top-6 right-6 w-24 h-24 border border-emerald-400/20 rounded-2xl rotate-12 animate-pulse"></div>
              <div className="absolute bottom-6 left-6 w-16 h-16 border border-teal-400/20 rounded-full animate-spin" style={{animationDuration: '25s'}}></div>
              
              <CardHeader className="relative text-center pb-8">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-emerald-500 via-teal-600 to-cyan-700 rounded-3xl shadow-2xl mb-6 mx-auto relative">
                  <Upload className="h-10 w-10 text-white" />
                  <div className="absolute -inset-1 bg-gradient-to-r from-emerald-400 to-cyan-600 rounded-3xl blur opacity-30 animate-pulse"></div>
                </div>
                <CardTitle className="text-4xl font-bold bg-gradient-to-r from-white via-emerald-200 to-teal-200 bg-clip-text text-transparent mb-4">
                  上传素材
                </CardTitle>
                <p className="text-gray-300 text-lg leading-relaxed max-w-2xl mx-auto">支持多种格式的图片和视频文件，智能处理高达20个文件，开启您的3D重建之旅</p>
              </CardHeader>
              <CardContent className="relative">
                <FileUpload
                  onFilesChange={handleFilesChange}
                  maxFiles={20}
                  maxFileSize={500}
                />
              </CardContent>
            </Card>

            {/* 开始处理按钮 */}
            {files.length > 0 && (
              <div className="flex justify-center pt-12">
                <div className="relative group">
                  {/* 多层光晕效果 */}
                  <div className="absolute -inset-2 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 rounded-3xl blur-2xl opacity-40 group-hover:opacity-80 transition duration-1000 animate-pulse"></div>
                  <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-700 rounded-3xl blur-lg opacity-60 group-hover:opacity-100 transition duration-700"></div>
                  
                  <Button
                    onClick={startReconstruction}
                    size="lg"
                    className="relative px-20 py-8 text-2xl font-bold bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-700 hover:from-cyan-400 hover:via-blue-500 hover:to-purple-600 text-white shadow-2xl hover:shadow-cyan-500/50 transform hover:scale-105 transition-all duration-700 rounded-3xl border border-white/20 backdrop-blur-sm"
                  >
                    <div className="flex items-center space-x-6">
                      <div className="relative">
                        <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm group-hover:bg-white/30 transition-all duration-500 group-hover:rotate-12">
                          <Play className="h-7 w-7 text-white group-hover:scale-125 transition-transform duration-500" />
                        </div>
                        <div className="absolute -inset-1 bg-white/10 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                      </div>
                      <div className="flex flex-col items-start">
                        <span className="tracking-wide text-left">启动 AI 重建</span>
                        <span className="text-sm text-white/80 font-normal tracking-normal">Neural Reconstruction Engine</span>
                      </div>
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-white rounded-full animate-ping"></div>
                        <div className="w-2 h-2 bg-white/60 rounded-full animate-ping" style={{animationDelay: '0.2s'}}></div>
                        <div className="w-2 h-2 bg-white/40 rounded-full animate-ping" style={{animationDelay: '0.4s'}}></div>
                      </div>
                    </div>
                    
                    {/* 按钮内部动态光效 */}
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-white/20 via-transparent to-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white/40 to-transparent rounded-t-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'process' && currentTask && (
          <div className="max-w-6xl mx-auto space-y-8">
            {/* 现代化进度显示卡片 */}
            <Card className="border-0 shadow-2xl bg-black/40 backdrop-blur-2xl relative overflow-hidden border border-white/10">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-purple-500/5"></div>
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 animate-pulse"></div>
              
              {/* 动态背景装饰 */}
              <div className="absolute top-8 right-8 w-40 h-40 bg-gradient-to-br from-cyan-400/10 to-blue-400/10 rounded-full blur-3xl animate-pulse"></div>
              <div className="absolute bottom-8 left-8 w-32 h-32 bg-gradient-to-br from-purple-400/10 to-pink-400/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1.5s'}}></div>
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-gradient-to-br from-blue-400/5 to-purple-400/5 rounded-full blur-3xl animate-pulse" style={{animationDelay: '3s'}}></div>
              
              <CardHeader className="relative text-center pb-6">
                <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-cyan-500 via-blue-600 to-purple-700 rounded-3xl shadow-2xl mb-8 mx-auto relative">
                  <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                    <Cpu className="h-7 w-7 text-white animate-pulse" />
                  </div>
                  <div className="absolute -inset-2 bg-gradient-to-r from-cyan-400 to-purple-600 rounded-3xl blur opacity-30 animate-pulse"></div>
                </div>
                <CardTitle className="text-5xl font-bold bg-gradient-to-r from-white via-cyan-200 to-blue-200 bg-clip-text text-transparent mb-4">
                  AI 神经重建中
                </CardTitle>
                <p className="text-gray-300 text-xl leading-relaxed">正在使用前沿神经网络技术重建您的3D场景</p>
              </CardHeader>
              <CardContent className="space-y-12">
                {/* 大型圆形进度指示器 */}
                <div className="flex justify-center">
                  <div className="relative w-64 h-64">
                    {/* 外层光晕 */}
                    <div className="absolute -inset-4 bg-gradient-to-r from-cyan-400/20 via-blue-500/20 to-purple-600/20 rounded-full blur-2xl animate-pulse"></div>
                    
                    {/* SVG进度环 */}
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      {/* 背景圆环 */}
                      <circle
                        cx="50"
                        cy="50"
                        r="42"
                        stroke="rgba(255,255,255,0.1)"
                        strokeWidth="6"
                        fill="none"
                        className="drop-shadow-lg"
                      />
                      {/* 进度圆环 */}
                      <circle
                        cx="50"
                        cy="50"
                        r="42"
                        stroke="url(#modernProgressGradient)"
                        strokeWidth="6"
                        fill="none"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 42}`}
                        strokeDashoffset={`${2 * Math.PI * 42 * (1 - currentTask.progress / 100)}`}
                        className="transition-all duration-1000 ease-out drop-shadow-lg"
                      />
                      <defs>
                        <linearGradient id="modernProgressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#06b6d4" />
                          <stop offset="30%" stopColor="#3b82f6" />
                          <stop offset="70%" stopColor="#8b5cf6" />
                          <stop offset="100%" stopColor="#ec4899" />
                        </linearGradient>
                      </defs>
                    </svg>
                    
                    {/* 中心内容 */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <div className="text-6xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent mb-3">
                        {Math.round(currentTask.progress)}%
                      </div>
                      <div className="text-lg text-white/80 font-semibold tracking-wide">
                        {currentTask.status === 'completed' ? 'COMPLETED' :
                         currentTask.status === 'failed' ? 'FAILED' : 'PROCESSING'}
                      </div>
                      <div className="flex space-x-1 mt-2">
                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping"></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-ping" style={{animationDelay: '0.3s'}}></div>
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-ping" style={{animationDelay: '0.6s'}}></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 状态消息 */}
                <div className="text-center">
                  <div className="inline-flex items-center px-8 py-4 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/20 shadow-lg">
                    <div className={`w-4 h-4 rounded-full mr-4 ${
                      currentTask.status === 'completed' ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50' :
                      currentTask.status === 'failed' ? 'bg-red-400 animate-pulse shadow-lg shadow-red-400/50' :
                      'bg-cyan-400 animate-pulse shadow-lg shadow-cyan-400/50'
                    }`}></div>
                    <p className="text-white font-semibold text-lg">{currentTask.message}</p>
                  </div>
                </div>

                {/* 现代化信息网格 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-lg hover:bg-white/10 transition-all duration-500">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-white/60 mb-2 font-medium tracking-wide uppercase">重建算法</div>
                        <div className="text-2xl font-bold text-white">
                          {currentTask.method === '3dgs' ? '3D Gaussian Splatting' : 'Neural Radiance Fields'}
                        </div>
                        <div className="text-sm text-white/40 mt-1">
                          {currentTask.method === '3dgs' ? '实时神经渲染' : '体积神经渲染'}
                        </div>
                      </div>
                      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg ${
                        currentTask.method === '3dgs' ? 'bg-gradient-to-br from-cyan-500 to-blue-600' : 'bg-gradient-to-br from-purple-500 to-pink-600'
                      }`}>
                        <span className="text-white font-bold text-lg">
                          {currentTask.method === '3dgs' ? '3DGS' : 'NeRF'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-lg hover:bg-white/10 transition-all duration-500">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-white/60 mb-2 font-medium tracking-wide uppercase">输入数据</div>
                        <div className="text-2xl font-bold text-white">{currentTask.files.length} 个文件</div>
                        <div className="text-sm text-white/40 mt-1">多视角图像序列</div>
                      </div>
                      <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center shadow-lg">
                        <Upload className="h-8 w-8 text-white" />
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-lg hover:bg-white/10 transition-all duration-500">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-white/60 mb-2 font-medium tracking-wide uppercase">开始时间</div>
                        <div className="text-2xl font-bold text-white">{currentTask.createdAt.toLocaleTimeString()}</div>
                        <div className="text-sm text-white/40 mt-1">{currentTask.createdAt.toLocaleDateString()}</div>
                      </div>
                      <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl flex items-center justify-center shadow-lg">
                        <Play className="h-8 w-8 text-white" />
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-lg hover:bg-white/10 transition-all duration-500">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-white/60 mb-2 font-medium tracking-wide uppercase">处理状态</div>
                        <div className={`text-2xl font-bold ${
                          currentTask.status === 'completed' ? 'text-emerald-400' :
                          currentTask.status === 'failed' ? 'text-red-400' :
                          'text-cyan-400'
                        }`}>
                          {currentTask.status === 'completed' ? '处理完成' :
                           currentTask.status === 'failed' ? '处理失败' : '正在处理'}
                        </div>
                        <div className="text-sm text-white/40 mt-1">
                          {currentTask.status === 'completed' ? '重建成功' :
                           currentTask.status === 'failed' ? '请重试' : 'AI计算中'}
                        </div>
                      </div>
                      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg ${
                        currentTask.status === 'completed' ? 'bg-gradient-to-br from-emerald-500 to-green-600' :
                        currentTask.status === 'failed' ? 'bg-gradient-to-br from-red-500 to-red-600' :
                        'bg-gradient-to-br from-cyan-500 to-blue-600'
                      }`}>
                        <div className={`w-4 h-4 rounded-full ${
                          currentTask.status === 'completed' ? 'bg-white' :
                          currentTask.status === 'failed' ? 'bg-white' :
                          'bg-white animate-pulse'
                        }`}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'view' && (
          <div className="max-w-6xl mx-auto space-y-8">
            {/* 结果显示 */}
            {result && (
              <div className="relative">
                {/* 成功光晕效果 */}
                <div className="absolute -inset-6 bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-blue-500/20 rounded-3xl blur-3xl animate-pulse"></div>
                
                <div className="relative bg-black/40 backdrop-blur-2xl rounded-3xl p-12 border border-white/10 shadow-2xl">
                  {/* 成功状态指示器 */}
                  <div className="text-center mb-12">
                    <div className="inline-flex items-center space-x-6 bg-gradient-to-r from-emerald-500/10 via-cyan-500/10 to-blue-500/10 px-10 py-6 rounded-3xl border border-white/20 backdrop-blur-sm">
                      <div className="relative">
                        <div className="w-16 h-16 bg-gradient-to-r from-emerald-400 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg">
                          <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        </div>
                        <div className="absolute -inset-2 bg-emerald-400/30 rounded-2xl blur animate-pulse"></div>
                      </div>
                      <div className="flex flex-col items-start">
                        <span className="text-white font-bold text-3xl tracking-wide">重建完成</span>
                        <span className="text-emerald-300 text-lg font-medium">3D Reconstruction Complete</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* 主要内容区域 */}
                  <div className="space-y-10">
                    {/* 标题和描述 */}
                    <div className="text-center space-y-4">
                      <h3 className="text-5xl font-bold bg-gradient-to-r from-white via-cyan-200 to-emerald-200 bg-clip-text text-transparent">
                        3D 神经模型已生成
                      </h3>
                      <p className="text-xl text-white/80 leading-relaxed max-w-3xl mx-auto">
                        您的3D场景重建已成功完成，AI神经网络已生成高质量的三维模型，现在可以下载和预览结果
                      </p>
                    </div>
                    
                    {/* 模型信息卡片 */}
                    <div className="bg-white/5 rounded-2xl p-8 border border-white/10">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="text-center">
                          <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                            <Layers className="w-8 h-8 text-white" />
                          </div>
                          <div className="text-2xl font-bold text-white mb-2">高精度模型</div>
                          <div className="text-white/60">神经网络重建</div>
                        </div>
                        <div className="text-center">
                          <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                            <Eye className="w-8 h-8 text-white" />
                          </div>
                          <div className="text-2xl font-bold text-white mb-2">实时预览</div>
                          <div className="text-white/60">交互式查看</div>
                        </div>
                        <div className="text-center">
                           <div className="w-16 h-16 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                             <Settings className="w-8 h-8 text-white" />
                           </div>
                           <div className="text-2xl font-bold text-white mb-2">多格式导出</div>
                           <div className="text-white/60">通用格式支持</div>
                         </div>
                      </div>
                    </div>
                    
                    {/* 操作按钮 */}
                    <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-6">
                      <div className="relative group">
                        <div className="absolute -inset-1 bg-gradient-to-r from-emerald-400 via-cyan-500 to-blue-600 rounded-3xl blur opacity-60 group-hover:opacity-100 transition duration-700"></div>
                        <Button 
                           onClick={() => window.open(result.modelUrl, '_blank')}
                           className="relative px-12 py-6 text-xl font-bold bg-gradient-to-r from-emerald-500 via-cyan-600 to-blue-700 hover:from-emerald-400 hover:via-cyan-500 hover:to-blue-600 text-white shadow-2xl hover:shadow-emerald-500/50 transform hover:scale-105 transition-all duration-700 rounded-3xl border border-white/20 backdrop-blur-sm"
                         >
                           <div className="flex items-center space-x-4">
                             <div className="w-10 h-10 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm group-hover:bg-white/30 transition-all duration-500">
                               <Upload className="w-6 h-6 text-white group-hover:scale-110 transition-transform duration-500" />
                             </div>
                             <span className="tracking-wide">下载模型</span>
                           </div>
                         </Button>
                      </div>
                      
                      <div className="relative group">
                        <div className="absolute -inset-1 bg-gradient-to-r from-purple-400 via-pink-500 to-red-600 rounded-3xl blur opacity-60 group-hover:opacity-100 transition duration-700"></div>
                        <Button 
                           onClick={() => window.open(result.modelUrl, '_blank')}
                           className="relative px-12 py-6 text-xl font-bold bg-gradient-to-r from-purple-500 via-pink-600 to-red-700 hover:from-purple-400 hover:via-pink-500 hover:to-red-600 text-white shadow-2xl hover:shadow-purple-500/50 transform hover:scale-105 transition-all duration-700 rounded-3xl border border-white/20 backdrop-blur-sm"
                         >
                           <div className="flex items-center space-x-4">
                             <div className="w-10 h-10 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm group-hover:bg-white/30 transition-all duration-500">
                               <Eye className="w-6 h-6 text-white group-hover:scale-110 transition-transform duration-500" />
                             </div>
                             <span className="tracking-wide">预览模型</span>
                           </div>
                         </Button>
                      </div>
                    </div>
                    
                    {/* 额外信息 */}
                    <div className="text-center pt-6">
                      <div className="inline-flex items-center space-x-2 text-white/60">
                        <div className="w-2 h-2 bg-emerald-400 rounded-full animate-ping"></div>
                        <span className="text-sm font-medium">模型已优化并准备就绪</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* 3D场景显示 */}
            <div className="h-[calc(100vh-400px)] min-h-[600px]">
              <Scene3D
                result={result || undefined}
                loading={currentTask?.status === 'processing'}
                error={currentTask?.status === 'failed' ? currentTask.message : undefined}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
