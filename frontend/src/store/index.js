import { createStore } from 'vuex'
import apiClient from '../api/client'

export default createStore({
  state: {
    userId: localStorage.getItem('userId') || null,
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
    },
    SET_AI_STATUS(state, status) {
      state.aiStatus = status
    },
    ADD_MESSAGE(state, message) {
      state.messages.push(message)
    },
    SET_MESSAGES(state, messages) {
      state.messages = messages
    },
    SET_CURRENT_QUESTION(state, question) {
      state.currentQuestion = question
    },
    SET_QUIZ_PROGRESS(state, progress) {
      state.quizProgress = progress
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    CLEAR_SESSION(state) {
      state.userId = null
      state.messages = []
      state.aiStatus = 'idle'
      state.currentQuestion = null
      state.quizProgress = null
      localStorage.removeItem('userId')
    }
  },
  actions: {
    async createSession({ commit }) {
      try {
        commit('SET_LOADING', true)
        const response = await apiClient.createSession()
        commit('SET_USER_ID', response.user_id)
        commit('ADD_MESSAGE', {
          role: 'agent',
          content: response.greeting,
          timestamp: new Date().toISOString()
        })
        commit('SET_AI_STATUS', 'idle')
        return response
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async sendMessage({ commit, state }, message) {
      try {
        commit('SET_LOADING', true)
        commit('SET_AI_STATUS', 'thinking')
        
        // 添加用户消息到列表
        commit('ADD_MESSAGE', {
          role: 'user',
          content: message,
          timestamp: new Date().toISOString()
        })
        
        const response = await apiClient.sendMessage(state.userId, message)
        
        // 添加AI回复到列表
        commit('ADD_MESSAGE', {
          role: 'agent',
          content: response.message,
          timestamp: new Date().toISOString()
        })
        
        // 更新AI状态
        if (response.status === 'quiz') {
          commit('SET_AI_STATUS', 'quiz')
          if (response.quiz_info) {
            commit('SET_CURRENT_QUESTION', response.quiz_info)
            commit('SET_QUIZ_PROGRESS', response.quiz_info)
          }
        } else {
          // 根据消息内容设置不同的表情状态
          if (response.message.includes('哈哈') || response.message.includes('呱呱')) {
            commit('SET_AI_STATUS', 'happy')
          } else if (response.message.includes('？') || response.message.includes('!')) {
            commit('SET_AI_STATUS', 'surprised')
          } else {
            commit('SET_AI_STATUS', 'idle')
          }
        }
        
        return response
      } catch (error) {
        commit('SET_ERROR', error.message)
        commit('SET_AI_STATUS', 'idle')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async submitAnswer({ commit, state }, answer) {
      try {
        commit('SET_LOADING', true)
        commit('SET_AI_STATUS', 'thinking')
        
        // 添加用户回答到列表
        commit('ADD_MESSAGE', {
          role: 'user',
          content: answer,
          timestamp: new Date().toISOString()
        })
        
        const response = await apiClient.submitAnswer(state.userId, answer)
        
        // 添加AI回复到列表
        commit('ADD_MESSAGE', {
          role: 'agent',
          content: response.message,
          timestamp: new Date().toISOString()
        })
        
        // 更新问题信息
        if (response.quiz_info) {
          commit('SET_CURRENT_QUESTION', response.quiz_info)
          commit('SET_QUIZ_PROGRESS', response.quiz_info)
        }
        
        // 设置AI状态
        if (response.status === 'chat') {
          commit('SET_AI_STATUS', 'happy')
        } else {
          commit('SET_AI_STATUS', 'quiz')
        }
        
        return response
      } catch (error) {
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
        commit('SET_LOADING', true)
        const history = await apiClient.getHistory(state.userId)
        commit('SET_MESSAGES', history)
        return history
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    logout({ commit }) {
      commit('CLEAR_SESSION')
    }
  }
}) 