import { createStore } from 'vuex'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

export default createStore({
  state: {
    questions: [],
    currentQuestionIndex: 0,
    userAnswers: {},
    feedbacks: {},
    isLoading: false,
    error: null,
    quizCompleted: false,
    finalFeedback: '',
    finalFeedbackAudio: null,
    correctCount: 0,
    audioEnabled: true
  },
  
  getters: {
    currentQuestion(state) {
      return state.questions[state.currentQuestionIndex] || null
    },
    totalQuestions(state) {
      return state.questions.length
    },
    progress(state) {
      return (state.currentQuestionIndex / state.questions.length) * 100
    },
    isLastQuestion(state) {
      return state.currentQuestionIndex === state.questions.length - 1
    },
    getUserAnswer: (state) => (questionId) => {
      return state.userAnswers[questionId] || ''
    },
    getFeedback: (state) => (questionId) => {
      return state.feedbacks[questionId] || null
    }
  },
  
  mutations: {
    SET_QUESTIONS(state, questions) {
      state.questions = questions
    },
    SET_LOADING(state, isLoading) {
      state.isLoading = isLoading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    SET_USER_ANSWER(state, { questionId, answer }) {
      state.userAnswers = { ...state.userAnswers, [questionId]: answer }
    },
    SET_FEEDBACK(state, { questionId, feedback, isCorrect, feedbackAudio }) {
      state.feedbacks = { 
        ...state.feedbacks, 
        [questionId]: { text: feedback, isCorrect, audio: feedbackAudio } 
      }
      
      if (isCorrect) {
        state.correctCount += 1
      }
    },
    NEXT_QUESTION(state) {
      if (state.currentQuestionIndex < state.questions.length - 1) {
        state.currentQuestionIndex += 1
      }
    },
    PREV_QUESTION(state) {
      if (state.currentQuestionIndex > 0) {
        state.currentQuestionIndex -= 1
      }
    },
    RESET_QUIZ(state) {
      state.currentQuestionIndex = 0
      state.userAnswers = {}
      state.feedbacks = {}
      state.quizCompleted = false
      state.finalFeedback = ''
      state.finalFeedbackAudio = null
      state.correctCount = 0
    },
    SET_QUIZ_COMPLETED(state, completed) {
      state.quizCompleted = completed
    },
    SET_FINAL_FEEDBACK(state, { feedback, feedbackAudio }) {
      state.finalFeedback = feedback
      state.finalFeedbackAudio = feedbackAudio
    },
    toggleAudio(state) {
      state.audioEnabled = !state.audioEnabled;
    }
  },
  
  actions: {
    async fetchQuestions({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const response = await axios.get(`${API_BASE_URL}/questions`)
        if (response.data.success) {
          commit('SET_QUESTIONS', response.data.questions)
        } else {
          commit('SET_ERROR', '获取题目失败')
        }
      } catch (error) {
        console.error('Error fetching questions:', error)
        commit('SET_ERROR', '获取题目失败: ' + error.message)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async submitAnswer({ commit, state }, { questionId, answer, questionType, question, correctAnswer }) {
      commit('SET_USER_ANSWER', { questionId, answer })
      
      try {
        const response = await axios.post(`${API_BASE_URL}/check-answer`, {
          question_id: questionId,
          question_type: questionType,
          answer: answer,
          question: question,
          correct_answer: correctAnswer
        })
        
        if (response.data.success) {
          commit('SET_FEEDBACK', { 
            questionId, 
            feedback: response.data.feedback, 
            isCorrect: response.data.is_correct,
            feedbackAudio: response.data.feedback_audio 
          })
        }
      } catch (error) {
        console.error('Error checking answer:', error)
      }
    },
    
    async getFinalScore({ commit, state }) {
      if (state.quizCompleted) return
      
      try {
        const response = await axios.post(`${API_BASE_URL}/final-score`, {
          correct_count: state.correctCount,
          total_count: state.questions.length
        })
        
        if (response.data.success) {
          commit('SET_QUIZ_COMPLETED', true)
          commit('SET_FINAL_FEEDBACK', { 
            feedback: response.data.feedback,
            feedbackAudio: response.data.feedback_audio
          })
        }
      } catch (error) {
        console.error('Error getting final score:', error)
      }
    },
    
    resetQuiz({ commit }) {
      commit('RESET_QUIZ')
      commit('SET_QUESTIONS', [])
    }
  }
}) 