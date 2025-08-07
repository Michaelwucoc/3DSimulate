import React, { useCallback, useState } from 'react'
import { Upload, X, FileVideo, Image, AlertCircle } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent } from './ui/card'
import { Progress } from './ui/progress'
import type { UploadFile } from '../types'
import { formatFileSize, isValidVideoFile, isValidImageFile, generateId } from '../lib/utils'

interface FileUploadProps {
  onFilesChange: (files: UploadFile[]) => void
  maxFiles?: number
  maxFileSize?: number // MB
  acceptedTypes?: string[]
  disabled?: boolean
}

export function FileUpload({
  onFilesChange,
  maxFiles = 10,
  maxFileSize = 500,
  acceptedTypes = ['video/*', 'image/*'],
  disabled = false
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFile = useCallback((file: File): string | null => {
    // 检查文件大小
    if (file.size > maxFileSize * 1024 * 1024) {
      return `文件大小不能超过 ${maxFileSize}MB`
    }

    // 检查文件类型
    const isVideo = isValidVideoFile(file)
    const isImage = isValidImageFile(file)
    
    if (!isVideo && !isImage) {
      return '只支持视频文件（MP4, AVI, MOV, MKV, WebM）和图片文件（JPEG, PNG, WebP, BMP）'
    }

    return null
  }, [maxFileSize])

  const processFiles = useCallback(async (fileList: FileList) => {
    const newFiles: UploadFile[] = []
    const errors: string[] = []

    // 检查文件数量限制
    if (files.length + fileList.length > maxFiles) {
      setError(`最多只能上传 ${maxFiles} 个文件`)
      return
    }

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i]
      const validationError = validateFile(file)
      
      if (validationError) {
        errors.push(`${file.name}: ${validationError}`)
        continue
      }

      // 创建预览
      let preview: string | undefined
      if (isValidImageFile(file)) {
        preview = URL.createObjectURL(file)
      }

      const uploadFile: UploadFile = {
        id: generateId(),
        name: file.name,
        size: file.size,
        type: isValidVideoFile(file) ? 'video' : 'image',
        file,
        preview,
        uploadedAt: new Date(),
        progress: 0
      }

      newFiles.push(uploadFile)
    }

    if (errors.length > 0) {
      setError(errors.join('\n'))
    } else {
      setError(null)
    }

    if (newFiles.length > 0) {
      const updatedFiles = [...files, ...newFiles]
      setFiles(updatedFiles)
      onFilesChange(updatedFiles)
    }
  }, [files, maxFiles, validateFile, onFilesChange])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    
    if (disabled) return
    
    const droppedFiles = e.dataTransfer.files
    if (droppedFiles.length > 0) {
      processFiles(droppedFiles)
    }
  }, [disabled, processFiles])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setDragOver(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files
    if (selectedFiles && selectedFiles.length > 0) {
      processFiles(selectedFiles)
    }
    // 清空input值，允许重复选择同一文件
    e.target.value = ''
  }, [processFiles])

  const removeFile = useCallback((fileId: string) => {
    const updatedFiles = files.filter(f => f.id !== fileId)
    setFiles(updatedFiles)
    onFilesChange(updatedFiles)
    
    // 清理预览URL
    const fileToRemove = files.find(f => f.id === fileId)
    if (fileToRemove?.preview) {
      URL.revokeObjectURL(fileToRemove.preview)
    }
  }, [files, onFilesChange])

  const clearAll = useCallback(() => {
    // 清理所有预览URL
    files.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview)
      }
    })
    
    setFiles([])
    onFilesChange([])
    setError(null)
  }, [files, onFilesChange])

  return (
    <div className="space-y-4">
      {/* 上传区域 */}
      <div
        className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
          dragOver 
            ? 'border-blue-400 bg-blue-50/50 scale-[1.02]' 
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50/50'
        } ${
          disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !disabled && document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
        />
        
        <div className={`transition-all duration-300 ${
          dragOver ? 'transform scale-110' : ''
        }`}>
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-6">
            <Upload className="h-8 w-8 text-white" />
          </div>
          
          <h3 className="text-xl font-bold text-gray-900 mb-3">上传您的文件</h3>
          <p className="text-gray-600 mb-2 text-lg">
            拖拽文件到此处，或点击选择文件
          </p>
          <p className="text-sm text-gray-500 mb-6">
            支持视频和图片文件，最大 {maxFileSize}MB，最多 {maxFiles} 个文件
          </p>
          
          {!disabled && (
            <Button 
              type="button" 
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-8 py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
            >
              选择文件
            </Button>
          )}
        </div>
      </div>

      {/* 错误信息 */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-2 text-destructive">
              <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
              <div className="text-sm whitespace-pre-line">{error}</div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 文件列表 */}
      {files.length > 0 && (
        <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                已选择文件 ({files.length})
              </h4>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={clearAll}
                disabled={disabled}
                className="hover:bg-red-50 hover:border-red-300 hover:text-red-600 transition-colors"
              >
                清空全部
              </Button>
            </div>
            
            <div className="grid gap-4">
              {files.map((file, index) => (
                <div
                  key={file.id}
                  className="group flex items-center space-x-4 p-4 border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-md transition-all duration-300 bg-white"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {/* 文件图标/预览 */}
                  <div className="flex-shrink-0 relative">
                    {file.type === 'image' && file.preview ? (
                      <div className="relative">
                        <img
                          src={file.preview}
                          alt={file.name}
                          className="h-16 w-16 object-cover rounded-xl shadow-sm"
                        />
                        <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                          <Image className="h-3 w-3 text-white" />
                        </div>
                      </div>
                    ) : file.type === 'video' ? (
                      <div className="h-16 w-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-sm">
                        <FileVideo className="h-8 w-8 text-white" />
                      </div>
                    ) : (
                      <div className="h-16 w-16 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-sm">
                        <Image className="h-8 w-8 text-white" />
                      </div>
                    )}
                  </div>
                  
                  {/* 文件信息 */}
                  <div className="flex-1 min-w-0">
                    <p className="text-base font-semibold text-gray-900 truncate mb-1">{file.name}</p>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                        {formatFileSize(file.size)}
                      </span>
                      <span className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                        {file.type === 'video' ? '视频文件' : '图片文件'}
                      </span>
                    </div>
                    
                    {/* 上传进度 */}
                    {typeof file.progress === 'number' && file.progress < 100 && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-blue-600">上传中...</span>
                          <span className="text-xs font-medium text-blue-600">{file.progress}%</span>
                        </div>
                        <Progress value={file.progress} className="h-2 bg-blue-100" />
                      </div>
                    )}
                  </div>
                  
                  {/* 删除按钮 */}
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeFile(file.id)}
                    disabled={disabled}
                    className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50 hover:text-red-600"
                  >
                    <X className="h-5 w-5" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}