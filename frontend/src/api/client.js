import axios from 'axios'

const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// 响应拦截器，只处理JSON字符串的格式化解析
apiClient.interceptors.response.use(response => {
  // 检查是否有message字段且看起来像JSON字符串
  if (response.data && response.data.message) {
    try {
      // 如果消息中包含代码块，尝试从中提取JSON
      if (response.data.message.includes('```json') && response.data.message.includes('```')) {
        const jsonMatch = response.data.message.match(/```json([\s\S]*?)```/)
        if (jsonMatch && jsonMatch[1]) {
          const parsedJson = JSON.parse(jsonMatch[1].trim())
          if (parsedJson.message) {
            // 替换原始message
            response.data.message = parsedJson.message
            
            // 如果有其他字段，也复制过来
            if (parsedJson.status) {
              response.data.status = parsedJson.status
            }
            if (parsedJson.quiz_info) {
              response.data.quiz_info = parsedJson.quiz_info
            }
          }
        }
      } 
      // 如果整个message就是一个JSON字符串
      else if (response.data.message.trim().startsWith('{') && response.data.message.trim().endsWith('}')) {
        const parsedJson = JSON.parse(response.data.message)
        if (parsedJson.message) {
          // 更新响应对象
          response.data.message = parsedJson.message
          if (parsedJson.status) {
            response.data.status = parsedJson.status
          }
          if (parsedJson.quiz_info) {
            response.data.quiz_info = parsedJson.quiz_info
          }
        }
      }
    } catch (error) {
      console.error('解析JSON响应失败:', error)
    }
  }
  
  return response
})

export default {
  // 创建聊天会话
  async createSession(roleCardId = process.env.VUE_APP_DEFAULT_ROLE || 'evil_frog') {
    const response = await apiClient.post('/chat/create_session', {
      role_card_id: roleCardId
    })
    return response.data
  },
  
  // 发送消息
  async sendMessage(userId, message) {
    const response = await apiClient.post('/chat/send', {
      user_id: userId,
      message
    })
    
    return response.data
  },
  
  // 获取聊天历史
  async getHistory(userId, limit = 50) {
    const response = await apiClient.get(`/chat/history/${userId}?limit=${limit}`)
    return response.data
  },
  
  // 删除会话
  async deleteSession(userId) {
    const response = await apiClient.delete(`/chat/session/${userId}`)
    return response.data
  },
  
  // 获取角色卡列表
  async getRoleCards() {
    const response = await apiClient.get('/chat/role_cards')
    return response.data
  },
  
  // 开始答题
  async startQuiz(userId, totalQuestions = 3) {
    try {
      const response = await apiClient.post('/quiz/start', {
        user_id: userId,
        total_questions: totalQuestions
      })
      return response.data
    } catch (error) {
      console.error('无法启动答题:', error);
      throw error;
    }
  },
  
  // 提交答案
  async submitAnswer(userId, answer) {
    const response = await apiClient.post('/quiz/answer', {
      user_id: userId,
      answer
    })
    return response.data
  },
  
  // 获取下一题
  async getNextQuestion(userId) {
    const response = await apiClient.get(`/quiz/next/${userId}`)
    return response.data
  },
  
  // 结束答题
  async endQuiz(userId) {
    const response = await apiClient.post(`/quiz/end/${userId}`)
    return response.data
  },
  
  // 获取答题进度
  async getQuizProgress(userId) {
    const response = await apiClient.get(`/quiz/progress/${userId}`)
    return response.data
  }
} 