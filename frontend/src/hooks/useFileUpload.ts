import { useState, useCallback } from 'react'
import { UploadFile } from '../types'
import { isValidVideoFile, isValidImageFile, formatFileSize } from '../lib/utils'

interface UseFileUploadOptions {
  maxFiles?: number
  maxFileSize?: number // in bytes
  allowedTypes?: ('video' | 'image')[]
}

export function useFileUpload(options: UseFileUploadOptions = {}) {
  const {
    maxFiles = 10,
    maxFileSize = 500 * 1024 * 1024, // 500MB
    allowedTypes = ['video', 'image']
  } = options

  const [files, setFiles] = useState<UploadFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFile = useCallback((file: File): string | null => {
    // 检查文件大小
    if (file.size > maxFileSize) {
      return `文件 ${file.name} 太大，最大允许 ${formatFileSize(maxFileSize)}`
    }

    // 检查文件类型
    const isVideo = isValidVideoFile(file)
    const isImage = isValidImageFile(file)

    if (!isVideo && !isImage) {
      return `不支持的文件类型: ${file.type}`
    }

    if (isVideo && !allowedTypes.includes('video')) {
      return '不支持视频文件上传'
    }

    if (isImage && !allowedTypes.includes('image')) {
      return '不支持图片文件上传'
    }

    return null
  }, [maxFileSize, allowedTypes])

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    setError(null)
    const fileArray = Array.from(newFiles)
    
    // 检查文件数量限制
    if (files.length + fileArray.length > maxFiles) {
      setError(`最多只能上传 ${maxFiles} 个文件`)
      return
    }

    const validFiles: UploadFile[] = []
    const errors: string[] = []

    fileArray.forEach(file => {
      const validationError = validateFile(file)
      if (validationError) {
        errors.push(validationError)
        return
      }

      const uploadFile: UploadFile = {
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: isValidVideoFile(file) ? 'video' : 'image',
        file,
        uploadedAt: new Date()
      }

      // 为图片文件生成预览
      if (uploadFile.type === 'image') {
        const reader = new FileReader()
        reader.onload = (e) => {
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id 
              ? { ...f, preview: e.target?.result as string }
              : f
          ))
        }
        reader.readAsDataURL(file)
      }

      validFiles.push(uploadFile)
    })

    if (errors.length > 0) {
      setError(errors.join('\n'))
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles])
    }
  }, [files.length, maxFiles, validateFile])

  const removeFile = useCallback((fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }, [])

  const clearFiles = useCallback(() => {
    setFiles([])
    setError(null)
  }, [])

  const uploadFiles = useCallback(async (): Promise<string[]> => {
    if (files.length === 0) {
      setError('没有文件需要上传')
      return []
    }

    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      files.forEach(file => {
        formData.append('files', file.file)
      })

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`上传失败: ${response.statusText}`)
      }

      const result = await response.json()
      setIsUploading(false)
      return result.fileIds || []

    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
      setIsUploading(false)
      return []
    }
  }, [files])

  return {
    files,
    isUploading,
    error,
    addFiles,
    removeFile,
    clearFiles,
    uploadFiles
  }
} 