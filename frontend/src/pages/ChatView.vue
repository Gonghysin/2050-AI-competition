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
            <label :class="{ selected: userAnswer === String.fromCharCode(65 + index) }">
              <input 
                type="radio" 
                :value="String.fromCharCode(65 + index)" 
                v-model="userAnswer"
                :disabled="loading"
              >
              <span class="option-label">{{ String.fromCharCode(65 + index) }}</span>
              <span class="option-text">{{ option }}</span>
            </label>
          </div>
        </div>
        
        <!-- 判断题 -->
        <div v-else-if="questionType === 'tf'" class="tf-question">
          <label :class="{ selected: userAnswer === 'T' }">
            <input type="radio" value="T" v-model="userAnswer" :disabled="loading">
            <span class="tf-button">是</span>
          </label>
          <label :class="{ selected: userAnswer === 'F' }">
            <input type="radio" value="F" v-model="userAnswer" :disabled="loading">
            <span class="tf-button">否</span>
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
        
        <!-- 答题按钮区域 -->
        <div class="quiz-actions">
          <button 
            v-if="!showAnswer"
            @click="submitAnswer" 
            class="btn submit-btn" 
            :disabled="!userAnswer || loading"
          >
            提交答案
          </button>
        
          <!-- 显示答案和下一题按钮 -->
          <div v-if="showAnswer" class="answer-section">
            <div class="correct-answer">
              <strong>正确答案:</strong> {{ getFormattedAnswer() }}
            </div>
            <button 
              @click="getNextQuestion" 
              class="btn next-btn"
              :disabled="loading"
            >
              下一题
            </button>
          </div>
        </div>
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
      userAnswer: null,
      showAnswer: false
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
        this.showAnswer = false;
      }
    },
    currentQuestion(newVal) {
      // 新题目时重置显示答案状态
      if (newVal) {
        this.showAnswer = false;
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
        // 提交答案后显示正确答案
        this.showAnswer = true;
      } catch (error) {
        console.error('提交答案失败:', error);
        alert('提交答案失败，请重试');
      }
    },
    async getNextQuestion() {
      try {
        // 直接获取下一题
        await this.$store.dispatch('getNextQuestion');
        this.userAnswer = null;
      } catch (error) {
        console.error('获取下一题失败:', error);
        alert('获取下一题失败，请重试');
      }
    },
    logout() {
      this.$store.dispatch('logout');
      this.userMessage = '';
      this.userAnswer = null;
      this.showAnswer = false;
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
    },
    getFormattedAnswer() {
      if (!this.currentQuestion || !this.currentQuestion.answer) {
        return '';
      }
      
      const answer = this.currentQuestion.answer;
      
      // 根据题目类型格式化答案
      if (this.questionType === 'choice' && this.currentQuestion.options) {
        const index = answer.charCodeAt(0) - 65; // 将A,B,C,D转为0,1,2,3
        if (index >= 0 && index < this.currentQuestion.options.length) {
          return `${answer}. ${this.currentQuestion.options[index]}`;
        }
      } else if (this.questionType === 'tf') {
        return answer === 'T' ? '是' : '否';
      }
      
      return answer;
    }
  },
  mounted() {
    // 清除之前的会话信息，显示欢迎界面
    this.$store.commit('CLEAR_SESSION');
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
  padding: 20px;
  margin: 15px 0;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.question-info {
  font-weight: bold;
  color: #4caf50;
  margin-bottom: 12px;
  font-size: 1.1rem;
}

.question-text {
  font-size: 1.1rem;
  line-height: 1.5;
  margin-bottom: 20px;
  padding: 0 5px;
}

.choice-question {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.choice-option label {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-radius: 10px;
  border: 1px solid #ddd;
  background-color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: #4caf50;
    background-color: #f1f8e9;
  }
  
  &.selected {
    border-color: #4caf50;
    background-color: #e8f5e9;
    box-shadow: 0 2px 4px rgba(76, 175, 80, 0.2);
  }
  
  input[type="radio"] {
    position: absolute;
    opacity: 0;
  }
  
  .option-label {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background-color: #4caf50;
    color: white;
    font-weight: bold;
    margin-right: 15px;
    flex-shrink: 0;
  }
  
  .option-text {
    font-size: 1rem;
  }
}

.tf-question {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
  
  label {
    position: relative;
    
    input[type="radio"] {
      position: absolute;
      opacity: 0;
    }
    
    .tf-button {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100px;
      height: 50px;
      border-radius: 25px;
      background-color: #fff;
      border: 1px solid #ddd;
      font-size: 1.1rem;
      cursor: pointer;
      transition: all 0.2s ease;
      
      &:hover {
        border-color: #4caf50;
        background-color: #f1f8e9;
      }
    }
    
    &.selected .tf-button {
      border-color: #4caf50;
      background-color: #4caf50;
      color: white;
      font-weight: bold;
      box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
    }
  }
}

.short-question {
  margin-bottom: 20px;
  
  textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 10px;
    resize: vertical;
    font-size: 1rem;
    transition: border-color 0.2s ease;
    
    &:focus {
      outline: none;
      border-color: #4caf50;
      box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
    }
  }
}

.quiz-actions {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.submit-btn {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s ease;
  min-width: 150px;
  
  &:hover:not(:disabled) {
    background-color: #388e3c;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  }
  
  &:disabled {
    background-color: #9e9e9e;
    cursor: not-allowed;
    opacity: 0.7;
  }
}

.answer-section {
  display: flex;
  flex-direction: column;
  width: 100%;
  margin-top: 15px;
  align-items: center;
}

.correct-answer {
  background-color: #e8f5e9;
  border: 1px solid #c8e6c9;
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 1rem;
  width: 100%;
  
  strong {
    color: #2e7d32;
  }
}

.next-btn {
  background-color: #2196f3;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 150px;
  
  &:hover {
    background-color: #1976d2;
    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
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