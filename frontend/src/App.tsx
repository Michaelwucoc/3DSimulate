import React, { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          3D场景重建平台
        </h1>
        <p className="text-gray-600 mb-6">
          欢迎使用3D场景重建平台！
        </p>
        <div className="space-y-4">
          <button
            onClick={() => setCount(count + 1)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition-colors"
          >
            点击次数: {count}
          </button>
          <p className="text-sm text-gray-500">
            如果您能看到这个页面，说明React应用正常运行！
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
