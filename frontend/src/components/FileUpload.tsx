import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Progress } from './ui/progress'
import { Upload, Video, Image, X, File, CheckCircle } from 'lucide-react'
import { useFileUpload } from '../hooks/useFileUpload'
import { formatFileSize } from '../lib/utils'

interface FileUploadProps {
  onUploadComplete?: (fileIds: string[]) => void
  onStartReconstruction?: (fileIds: string[]) => void
}

export function FileUpload({ onUploadComplete, onStartReconstruction }: FileUploadProps) {
  const {
    files,
    isUploading,
    error,
    addFiles,
    removeFile,
    clearFiles,
    uploadFiles
  } = useFileUpload({
    maxFiles: 10,
    maxFileSize: 500 * 1024 * 1024, // 500MB
    allowedTypes: ['video', 'image']
  })

  const [uploadProgress, setUploadProgress] = useState(0)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    addFiles(acceptedFiles)
  }, [addFiles])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    multiple: true
  })

  const handleUpload = async () => {
    setUploadProgress(0)
    const fileIds = await uploadFiles()
    
    if (fileIds.length > 0) {
      onUploadComplete?.(fileIds)
      // 模拟上传进度
      const interval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval)
            return 100
          }
          return prev + 10
        })
      }, 200)
    }
  }

  const handleStartReconstruction = () => {
    if (files.length > 0) {
      // 这里应该使用实际上传后的文件ID
      const fileIds = files.map(f => f.id)
      onStartReconstruction?.(fileIds)
    }
  }

  const getFileIcon = (type: 'video' | 'image') => {
    return type === 'video' ? <Video className="w-4 h-4" /> : <Image className="w-4 h-4" />
  }

  return (
    <div className="space-y-6">
      {/* 上传区域 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            上传文件
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`upload-area border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
              isDragActive ? 'dragover' : ''
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              {isDragActive ? '释放文件以上传' : '拖拽文件到此处或点击选择'}
            </p>
            <p className="text-sm text-gray-500">
              支持视频文件 (MP4, AVI, MOV, WMV, FLV, WEBM) 和图片文件 (JPEG, PNG, WEBP)
            </p>
            <p className="text-xs text-gray-400 mt-2">
              最大文件大小: 500MB，最多10个文件
            </p>
          </div>

          {/* 错误信息 */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {/* 上传进度 */}
          {isUploading && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>上传中...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="w-full" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* 文件列表 */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <File className="w-5 h-5" />
                已选择的文件 ({files.length})
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearFiles}
                  disabled={isUploading}
                >
                  清空
                </Button>
                <Button
                  size="sm"
                  onClick={handleUpload}
                  disabled={isUploading}
                >
                  {isUploading ? '上传中...' : '开始上传'}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getFileIcon(file.type)}
                    <div>
                      <p className="font-medium text-sm">{file.name}</p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)} • {file.type}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {file.preview && file.type === 'image' && (
                      <img
                        src={file.preview}
                        alt={file.name}
                        className="w-8 h-8 object-cover rounded"
                      />
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(file.id)}
                      disabled={isUploading}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {/* 开始重建按钮 */}
            {files.length > 0 && !isUploading && (
              <div className="mt-4 pt-4 border-t">
                <Button
                  onClick={handleStartReconstruction}
                  className="w-full"
                  size="lg"
                >
                  <CheckCircle className="w-5 h-5 mr-2" />
                  开始3D重建
                </Button>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  点击开始使用上传的文件进行3D场景重建
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
} 