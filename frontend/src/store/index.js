import { createStore } from 'vuex'
import apiClient from '../api/client'

// 确保每次页面加载时不保留之前的会话信息
localStorage.removeItem('userId')

export default createStore({
  state: {
    userId: null,
    messages: [],
    aiStatus: 'idle', // idle, thinking, quiz, happy, surprised
    currentQuestion: null,
    quizProgress: null,
    loading: false,
    error: null
  },
  getters: {
    isAuthenticated(state) {
      return !!state.userId
    },
    aiStatus(state) {
      return state.aiStatus
    },
    messages(state) {
      return state.messages
    },
    currentQuestion(state) {
      return state.currentQuestion
    },
    quizProgress(state) {
      return state.quizProgress
    }
  },
  mutations: {
    SET_USER_ID(state, userId) {
      state.userId = userId
      localStorage.setItem('userId', userId)
      console.log('[Store] 用户ID已设置:', userId)
    },
    SET_AI_STATUS(state, status) {
      console.log('[Store] AI状态变更:', state.aiStatus, '->', status)
      state.aiStatus = status
    },
    ADD_MESSAGE(state, message) {
      state.messages.push(message)
      console.log(`[Store] 添加消息 [${message.role}]: ${message.content.substring(0, 50)}${message.content.length > 50 ? '...' : ''}`)
    },
    SET_MESSAGES(state, messages) {
      state.messages = messages
      console.log(`[Store] 设置消息历史，共${messages.length}条`)
    },
    SET_CURRENT_QUESTION(state, question) {
      state.currentQuestion = question
      if (question) {
        console.log('[Store] 当前题目已更新:', 
          `类型=${question.question_type || '未知'}`, 
          `步骤=${question.step || 0}/${question.total || 0}`, 
          `题目=${question.question ? (question.question.substring(0, 30) + '...') : '无题目'}`
        )
      } else {
        console.log('[Store] 当前题目已清除')
      }
    },
    SET_QUIZ_PROGRESS(state, progress) {
      state.quizProgress = progress
      console.log('[Store] 答题进度已更新:', progress)
    },
    SET_LOADING(state, loading) {
      state.loading = loading
      console.log('[Store] 加载状态:', loading)
    },
    SET_ERROR(state, error) {
      state.error = error
      console.error('[Store] 错误:', error)
    },
    CLEAR_SESSION(state) {
      state.userId = null
      state.messages = []
      state.aiStatus = 'idle'
      state.currentQuestion = null
      state.quizProgress = null
      localStorage.removeItem('userId')
      console.log('[Store] 会话已清除')
    }
  },
  actions: {
    async createSession({ commit }) {
      try {
        console.log('[Action] 创建会话...')
        commit('SET_LOADING', true)
        const response = await apiClient.createSession()
        console.log('[Action] 创建会话成功:', response)
        commit('SET_USER_ID', response.user_id)
        commit('ADD_MESSAGE', {
          role: 'agent',
          content: response.greeting,
          timestamp: new Date().toISOString()
        })
        commit('SET_AI_STATUS', 'idle')
        return response
      } catch (error) {
        console.error('[Action] 创建会话失败:', error)
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async sendMessage({ commit, state }, message) {
      try {
        console.log('[Action] 发送消息:', message)
        commit('SET_LOADING', true)
        commit('SET_AI_STATUS', 'thinking')
        
        // 添加用户消息到列表
        commit('ADD_MESSAGE', {
          role: 'user',
          content: message,
          timestamp: new Date().toISOString()
        })
        
        // 直接发送消息到后端，让后端处理状态转换
        const response = await apiClient.sendMessage(state.userId, message)
        console.log('[Action] 收到后端响应:', JSON.stringify(response))
        
        // 添加AI回复到列表
        commit('ADD_MESSAGE', {
          role: 'agent',
          content: response.message,
          timestamp: new Date().toISOString()
        })
        
        // 根据后端返回的状态设置前端状态
        if (response.status === 'quiz') {
          console.log('[Action] 后端返回quiz状态，切换到答题模式')
          commit('SET_AI_STATUS', 'quiz')
          
          // 如果有quiz_info，更新当前问题
          if (response.quiz_info) {
            console.log('[Action] 更新题目信息:', response.quiz_info)
            commit('SET_CURRENT_QUESTION', response.quiz_info)
            commit('SET_QUIZ_PROGRESS', response.quiz_info)
          } else {
            console.warn('[Action] quiz状态但没有quiz_info')
          }
        } else {
          console.log('[Action] 保持聊天状态')
          // 聊天状态下的表情设置
          if (response.message.includes('哈哈') || response.message.includes('呱呱')) {
            commit('SET_AI_STATUS', 'happy')
          } else if (response.message.includes('？') || response.message.includes('!')) {
            commit('SET_AI_STATUS', 'surprised')
          } else {
            commit('SET_AI_STATUS', 'idle')
          }
          
          // 如果从quiz状态切换回chat状态，清除问题信息
          if (state.currentQuestion) {
            console.log('[Action] 从quiz切换回chat，清除问题信息')
            commit('SET_CURRENT_QUESTION', null)
            commit('SET_QUIZ_PROGRESS', null)
          }
        }
        
        return response
      } catch (error) {
        console.error('[Action] 发送消息失败:', error)
        commit('SET_ERROR', error.message)
        commit('SET_AI_STATUS', 'idle')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async submitAnswer({ commit, state }, answer) {
      try {
        console.log('[Action] 提交答案:', answer)
        commit('SET_LOADING', true)
        commit('SET_AI_STATUS', 'thinking')
        
        // 添加用户回答到列表
        commit('ADD_MESSAGE', {
          role: 'user',
          content: answer,
          timestamp: new Date().toISOString()
        })
        
        // 提交答案
        const response = await apiClient.submitAnswer(state.userId, answer)
        console.log('[Action] 答案反馈:', JSON.stringify(response))
        
        // 添加AI回复到列表
        commit('ADD_MESSAGE', {
          role: 'agent',
          content: response.message,
          timestamp: new Date().toISOString()
        })
        
        // 根据后端返回的状态更新前端状态
        if (response.status === 'quiz') {
          console.log('[Action] 继续答题模式')
          commit('SET_AI_STATUS', 'quiz')
          
          // 答对或答错时短暂显示相应状态
          if (response.quiz_info && response.quiz_info.user_answer) {
            const isCorrect = response.quiz_info.user_answer === response.quiz_info.answer
            console.log('[Action] 答案评判:', isCorrect ? '正确' : '错误')
            commit('SET_AI_STATUS', isCorrect ? 'correct' : 'wrong')
            
            // 2秒后恢复quiz状态
            setTimeout(() => {
              if (state.aiStatus === 'correct' || state.aiStatus === 'wrong') {
                console.log('[Action] 恢复答题状态')
                commit('SET_AI_STATUS', 'quiz')
              }
            }, 2000)
          }
          
          // 更新问题信息
          if (response.quiz_info) {
            console.log('[Action] 更新题目信息:', response.quiz_info)
            commit('SET_CURRENT_QUESTION', response.quiz_info)
            commit('SET_QUIZ_PROGRESS', response.quiz_info)
          }
        } else {
          console.log('[Action] 答题结束，切换回聊天模式')
          // 如果状态变为chat，清除问题信息
          commit('SET_AI_STATUS', 'idle')
          commit('SET_CURRENT_QUESTION', null)
          commit('SET_QUIZ_PROGRESS', null)
        }
        
        return response
      } catch (error) {
        console.error('[Action] 提交答案失败:', error)
        commit('SET_ERROR', error.message)
        commit('SET_AI_STATUS', 'idle')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async loadHistory({ commit, state }) {
      if (!state.userId) return
      
      try {
        console.log('[Action] 加载历史消息...')
        commit('SET_LOADING', true)
        const history = await apiClient.getHistory(state.userId)
        console.log(`[Action] 获取到${history.length}条历史消息`)
        commit('SET_MESSAGES', history)
        
        // 检查最近的消息，确定当前状态
        if (history && history.length > 0) {
          const lastAgentMessage = [...history].reverse().find(msg => msg.role === 'agent')
          if (lastAgentMessage) {
            console.log('[Action] 最后一条AI消息:', lastAgentMessage.content.substring(0, 50) + '...')
            // 获取当前状态
            try {
              console.log('[Action] 检查答题进度...')
              const quizProgress = await apiClient.getQuizProgress(state.userId)
              console.log('[Action] 答题进度:', quizProgress)
              if (quizProgress && quizProgress.status === 'in_progress') {
                console.log('[Action] 恢复答题模式')
                commit('SET_AI_STATUS', 'quiz')
                // 尝试获取当前题目
                console.log('[Action] 获取当前题目...')
                const nextQuestion = await apiClient.getNextQuestion(state.userId)
                console.log('[Action] 当前题目:', nextQuestion)
                if (nextQuestion && nextQuestion.quiz_info) {
                  commit('SET_CURRENT_QUESTION', nextQuestion.quiz_info)
                  commit('SET_QUIZ_PROGRESS', nextQuestion.quiz_info)
                }
              } else {
                // 默认为聊天状态
                console.log('[Action] 保持聊天模式')
                commit('SET_AI_STATUS', 'idle')
              }
            } catch (error) {
              console.error('[Action] 检查状态失败:', error)
              commit('SET_AI_STATUS', 'idle')
            }
          }
        }
        
        return history
      } catch (error) {
        console.error('[Action] 加载历史失败:', error)
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    logout({ commit }) {
      commit('CLEAR_SESSION')
      // 不立即创建新会话，而是回到欢迎界面让用户手动点击创建
    }
  }
}) 