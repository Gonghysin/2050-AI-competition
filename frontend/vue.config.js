module.exports = {
  devServer: {
    proxy: {
      '/api/chat/stream': {
        target: 'http://localhost:8001',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  lintOnSave: false // 禁用保存时的lint检查
} 