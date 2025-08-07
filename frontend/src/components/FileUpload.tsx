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
        className={`upload-area relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragOver ? 'dragover' : ''
        } ${
          disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-primary/50'
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
        
        <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">上传文件</h3>
        <p className="text-muted-foreground mb-4">
          拖拽文件到此处，或点击选择文件
        </p>
        <p className="text-sm text-muted-foreground">
          支持视频和图片文件，最大 {maxFileSize}MB，最多 {maxFiles} 个文件
        </p>
        
        {!disabled && (
          <Button type="button" variant="outline" className="mt-4">
            选择文件
          </Button>
        )}
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
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold">已选择文件 ({files.length})</h4>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={clearAll}
                disabled={disabled}
              >
                清空全部
              </Button>
            </div>
            
            <div className="space-y-3">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center space-x-3 p-3 border rounded-lg"
                >
                  {/* 文件图标/预览 */}
                  <div className="flex-shrink-0">
                    {file.type === 'image' && file.preview ? (
                      <img
                        src={file.preview}
                        alt={file.name}
                        className="h-12 w-12 object-cover rounded"
                      />
                    ) : file.type === 'video' ? (
                      <FileVideo className="h-12 w-12 text-blue-500" />
                    ) : (
                      <Image className="h-12 w-12 text-green-500" />
                    )}
                  </div>
                  
                  {/* 文件信息 */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.size)} • {file.type === 'video' ? '视频' : '图片'}
                    </p>
                    
                    {/* 上传进度 */}
                    {typeof file.progress === 'number' && file.progress < 100 && (
                      <div className="mt-2">
                        <Progress value={file.progress} className="h-2" />
                        <p className="text-xs text-muted-foreground mt-1">
                          上传中... {file.progress}%
                        </p>
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
                    className="flex-shrink-0"
                  >
                    <X className="h-4 w-4" />
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