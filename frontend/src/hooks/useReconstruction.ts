import { useState, useEffect, useCallback } from 'react'
import { ReconstructionTask, TaskStatusResponse } from '../types'

interface UseReconstructionOptions {
  pollInterval?: number // 轮询间隔，毫秒
  autoStart?: boolean
}

export function useReconstruction(options: UseReconstructionOptions = {}) {
  const { pollInterval = 2000, autoStart = false } = options

  const [tasks, setTasks] = useState<ReconstructionTask[]>([])
  const [currentTask, setCurrentTask] = useState<ReconstructionTask | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 创建新的重建任务
  const createTask = useCallback(async (fileIds: string[]): Promise<string | null> => {
    try {
      const response = await fetch('/api/reconstruction/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fileIds })
      })

      if (!response.ok) {
        throw new Error(`创建任务失败: ${response.statusText}`)
      }

      const result = await response.json()
      const taskId = result.taskId

      // 创建本地任务记录
      const newTask: ReconstructionTask = {
        id: taskId,
        status: 'pending',
        progress: 0,
        message: '任务已创建，等待处理...',
        files: [], // 这里可以从fileIds获取文件信息
        createdAt: new Date()
      }

      setTasks(prev => [...prev, newTask])
      setCurrentTask(newTask)

      if (autoStart) {
        startPolling(taskId)
      }

      return taskId

    } catch (err) {
      setError(err instanceof Error ? err.message : '创建任务失败')
      return null
    }
  }, [autoStart])

  // 开始轮询任务状态
  const startPolling = useCallback((taskId: string) => {
    setIsPolling(true)
    setError(null)

    const poll = async () => {
      try {
        const response = await fetch(`/api/reconstruction/status/${taskId}`)
        
        if (!response.ok) {
          throw new Error(`获取任务状态失败: ${response.statusText}`)
        }

        const result: TaskStatusResponse = await response.json()
        
        setTasks(prev => prev.map(task => 
          task.id === taskId 
            ? {
                ...task,
                status: result.status,
                progress: result.progress,
                message: result.message,
                result: result.result,
                completedAt: result.status === 'completed' ? new Date() : task.completedAt
              }
            : task
        ))

        setCurrentTask(prev => 
          prev?.id === taskId 
            ? {
                ...prev,
                status: result.status,
                progress: result.progress,
                message: result.message,
                result: result.result,
                completedAt: result.status === 'completed' ? new Date() : prev.completedAt
              }
            : prev
        )

        // 如果任务完成或失败，停止轮询
        if (result.status === 'completed' || result.status === 'failed') {
          setIsPolling(false)
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : '轮询任务状态失败')
        setIsPolling(false)
      }
    }

    // 立即执行一次
    poll()

    // 设置定时轮询
    const interval = setInterval(poll, pollInterval)

    // 清理函数
    return () => clearInterval(interval)
  }, [pollInterval])

  // 停止轮询
  const stopPolling = useCallback(() => {
    setIsPolling(false)
  }, [])

  // 获取任务列表
  const fetchTasks = useCallback(async () => {
    try {
      const response = await fetch('/api/reconstruction/tasks')
      
      if (!response.ok) {
        throw new Error(`获取任务列表失败: ${response.statusText}`)
      }

      const result = await response.json()
      setTasks(result.tasks || [])

    } catch (err) {
      setError(err instanceof Error ? err.message : '获取任务列表失败')
    }
  }, [])

  // 删除任务
  const deleteTask = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`/api/reconstruction/tasks/${taskId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error(`删除任务失败: ${response.statusText}`)
      }

      setTasks(prev => prev.filter(task => task.id !== taskId))
      
      if (currentTask?.id === taskId) {
        setCurrentTask(null)
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : '删除任务失败')
    }
  }, [currentTask])

  // 重新开始任务
  const restartTask = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`/api/reconstruction/tasks/${taskId}/restart`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`重新开始任务失败: ${response.statusText}`)
      }

      // 更新任务状态
      setTasks(prev => prev.map(task => 
        task.id === taskId 
          ? { ...task, status: 'pending', progress: 0, message: '任务重新开始...' }
          : task
      ))

      // 开始轮询
      startPolling(taskId)

    } catch (err) {
      setError(err instanceof Error ? err.message : '重新开始任务失败')
    }
  }, [startPolling])

  // 组件挂载时获取任务列表
  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  return {
    tasks,
    currentTask,
    isPolling,
    error,
    createTask,
    startPolling,
    stopPolling,
    fetchTasks,
    deleteTask,
    restartTask
  }
} 