import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

export default {
  // 创建聊天会话
  async createSession(roleCardId = 'evil_frog') {
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
    const response = await apiClient.post('/quiz/start', {
      user_id: userId,
      total_questions: totalQuestions
    })
    return response.data
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