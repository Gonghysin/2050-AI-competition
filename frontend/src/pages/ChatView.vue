<template>
  <div class="chat-container">
    <div class="chat-header">
      <h1>邪恶青蛙博士</h1>
      <button v-if="isAuthenticated" @click="logout" class="btn logout-btn">重置</button>
    </div>
    
    <!-- AI表情区域放在上方 -->
    <div class="emoji-section">
      <emoji-animation :status="aiStatus" />
    </div>
    
    <!-- AI输出区域 -->
    <div class="ai-output" v-if="isAuthenticated">
      <div class="ai-message">{{ currentAiMessage }}</div>
      
      <!-- 答题模式下的问题展示 -->
      <div v-if="aiStatus === 'quiz' && currentQuestion" class="question-container">
        <div class="question-info">
          第 {{ currentQuestion.step || 1 }}/{{ currentQuestion.total || 3 }} 题
        </div>
        
        <div class="question-text">{{ getQuestionText() }}</div>
        
        <!-- 选择题 -->
        <div v-if="questionType === 'choice'" class="choice-question">
          <div v-for="(option, index) in getQuestionOptions()" :key="index" class="choice-option">
            <label>
              <input 
                type="radio" 
                :value="String.fromCharCode(65 + index)" 
                v-model="userAnswer"
                :disabled="loading"
              >
              {{ String.fromCharCode(65 + index) }}. {{ option }}
            </label>
          </div>
        </div>
        
        <!-- 判断题 -->
        <div v-else-if="questionType === 'tf'" class="tf-question">
          <label>
            <input type="radio" value="是" v-model="userAnswer" :disabled="loading">
            是
          </label>
          <label>
            <input type="radio" value="否" v-model="userAnswer" :disabled="loading">
            否
          </label>
        </div>
        
        <!-- 简答题 -->
        <div v-else class="short-question">
          <textarea 
            v-model="userAnswer" 
            placeholder="请输入你的答案..." 
            rows="3"
            :disabled="loading"
          ></textarea>
        </div>
        
        <button 
          @click="submitAnswer" 
          class="btn submit-btn" 
          :disabled="!userAnswer || loading"
        >
          提交答案
        </button>
      </div>
    </div>
    
    <div v-if="!isAuthenticated" class="welcome-screen">
      <h2>欢迎来到AI答题系统</h2>
      <p>与邪恶青蛙博士聊天，或者挑战他的题目！</p>
      <button @click="createSession" class="btn start-btn">开始聊天</button>
    </div>
    
    <!-- 用户输入区域 -->
    <div class="input-container" v-if="isAuthenticated">
      <textarea 
        v-model="userMessage" 
        :placeholder="aiStatus === 'quiz' ? '请在上方选择答案并提交' : '输入你想说的话...'" 
        @keyup.enter="sendMessage"
        :disabled="loading || aiStatus === 'quiz'"
        rows="3"
      ></textarea>
      <button 
        @click="sendMessage" 
        class="btn send-btn" 
        :disabled="!userMessage.trim() || loading || aiStatus === 'quiz'"
      >
        发送
      </button>
    </div>
    
    <div class="loading-indicator" v-if="loading">
      <div class="spinner"></div>
      <span>AI思考中...</span>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapState } from 'vuex'
import EmojiAnimation from '../components/EmojiAnimation.vue'

export default {
  name: 'ChatView',
  components: {
    EmojiAnimation
  },
  data() {
    return {
      userMessage: '',
      userAnswer: null
    }
  },
  computed: {
    ...mapState([
      'loading',
      'currentQuestion',
      'error',
      'messages'
    ]),
    ...mapGetters([
      'isAuthenticated',
      'aiStatus'
    ]),
    currentAiMessage() {
      // 获取最后一条AI消息
      const aiMessages = this.messages.filter(msg => msg.role === 'agent');
      if (aiMessages.length > 0) {
        return aiMessages[aiMessages.length - 1].content;
      }
      return '';
    },
    questionType() {
      if (!this.currentQuestion) return 'choice';
      
      // 从currentQuestion或quiz_info中确定题目类型
      if (this.currentQuestion.question_type) {
        return this.currentQuestion.question_type;
      }
      
      // 如果有options但没有明确类型，判断为选择题
      if (this.currentQuestion.options && this.currentQuestion.options.length > 0) {
        return 'choice';
      }
      
      // 默认为简答题
      return 'short';
    }
  },
  watch: {
    aiStatus(newStatus) {
      if (newStatus !== 'quiz') {
        this.userAnswer = null;
      }
    }
  },
  methods: {
    async createSession() {
      try {
        await this.$store.dispatch('createSession');
      } catch (error) {
        console.error('创建会话失败:', error);
        alert('创建会话失败，请重试');
      }
    },
    async sendMessage() {
      if (!this.userMessage.trim() || this.loading) return;
      
      const message = this.userMessage.trim();
      this.userMessage = '';
      
      try {
        await this.$store.dispatch('sendMessage', message);
      } catch (error) {
        console.error('发送消息失败:', error);
        alert('发送消息失败，请重试');
      }
    },
    async submitAnswer() {
      if (!this.userAnswer || this.loading) return;
      
      try {
        await this.$store.dispatch('submitAnswer', this.userAnswer);
        this.userAnswer = null;
      } catch (error) {
        console.error('提交答案失败:', error);
        alert('提交答案失败，请重试');
      }
    },
    logout() {
      this.$store.dispatch('logout');
      this.userMessage = '';
      this.userAnswer = null;
    },
    getQuestionText() {
      if (!this.currentQuestion) return '';
      
      // 尝试从quiz_info中获取问题文本
      if (this.currentQuestion.question) {
        return this.currentQuestion.question;
      }
      
      return '请回答下面的问题';
    },
    getQuestionOptions() {
      if (!this.currentQuestion || !this.currentQuestion.options) {
        return [];
      }
      
      return this.currentQuestion.options;
    }
  },
  mounted() {
    if (this.isAuthenticated) {
      this.$store.dispatch('loadHistory');
    }
  }
}
</script>

<style scoped lang="scss">
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #4caf50;
  color: white;
  
  h1 {
    margin: 0;
    font-size: 1.5rem;
  }
  
  .logout-btn {
    background: #f44336;
    
    &:hover {
      background: darken(#f44336, 10%);
    }
  }
}

.emoji-section {
  padding: 20px 0;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  text-align: center;
}

.ai-output {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  
  .ai-message {
    font-size: 1.1rem;
    line-height: 1.6;
    padding: 16px;
    background: #f1f8e9;
    border-radius: 12px;
    max-width: 90%;
    margin-bottom: 20px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
}

.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 20px;
  
  h2 {
    margin-top: 0;
    color: #4caf50;
  }
  
  p {
    margin-bottom: 30px;
    color: #757575;
  }
  
  .start-btn {
    padding: 12px 30px;
    font-size: 1.1rem;
  }
}

.question-container {
  background: #f9fbe7;
  padding: 20px;
  border-radius: 12px;
  margin: 10px 0;
  width: 100%;
  max-width: 600px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  .question-info {
    font-weight: bold;
    margin-bottom: 10px;
    color: #4caf50;
  }
  
  .question-text {
    margin-bottom: 15px;
    font-size: 1.1rem;
    line-height: 1.5;
  }
  
  .choice-question, .tf-question, .short-question {
    margin: 15px 0;
  }
  
  .choice-option {
    margin-bottom: 10px;
  }
  
  label {
    display: block;
    padding: 8px;
    border-radius: 8px;
    cursor: pointer;
    text-align: left;
    
    &:hover {
      background: rgba(76, 175, 80, 0.1);
    }
    
    input {
      margin-right: 10px;
    }
  }
  
  textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 8px;
    resize: vertical;
    
    &:focus {
      border-color: #4caf50;
      outline: none;
    }
  }
  
  .submit-btn {
    margin-top: 15px;
    width: 100%;
  }
}

.input-container {
  display: flex;
  gap: 10px;
  padding: 15px;
  border-top: 1px solid #e0e0e0;
  background: #f5f5f5;
  
  textarea {
    flex: 1;
    resize: none;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px;
    font-size: 1rem;
    
    &:focus {
      outline: none;
      border-color: #4caf50;
    }
    
    &:disabled {
      background: #eee;
      color: #999;
    }
  }
  
  .send-btn {
    align-self: flex-end;
  }
}

.loading-indicator {
  position: fixed;
  bottom: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 10px 15px;
  border-radius: 20px;
  
  .spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s linear infinite;
    margin-right: 10px;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
}
</style> 