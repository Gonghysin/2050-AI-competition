<!-- eslint-disable -->
<template>
  <div class="app-container">
    <header>
      <h1>AI知识竞答</h1>
      <button @click="toggleAudio" class="audio-toggle">
        {{ audioEnabled ? '🔊' : '🔇' }}
      </button>
      <button @click="testAudio" class="test-audio-btn">测试音频</button>
    </header>
    
    <main>
      <div v-if="$store.state.error" class="error-message">
        {{ $store.state.error }}
        <button @click="retryFetchQuestions">重试</button>
      </div>
      
      <div v-else-if="$store.state.isLoading" class="loading">
        <div class="spinner"></div>
        <p>正在加载题目...</p>
      </div>
      
      <div v-else-if="!$store.state.quizStarted" class="welcome-screen">
        <h2>欢迎参加AI知识竞答!</h2>
        <p>测试你对人工智能的了解程度，共{{ $store.state.questions.length }}道题。</p>
        <p class="note">注意：语音朗读功能可能暂时不可用，但不影响答题。</p>
        <button @click="startQuiz" class="start-button">开始答题</button>
      </div>
      
      <div v-else-if="$store.state.quizFinished" class="results-screen">
        <h2>测验完成!</h2>
        <div class="score-container">
          <div class="score-circle">
            <span class="score-text">{{ $store.getters.score.percentage }}%</span>
          </div>
          <p>您答对了{{ $store.getters.score.correct }}/{{ $store.getters.score.total }}道题</p>
        </div>
        
        <div class="answers-review">
          <h3>答题详情</h3>
          <div v-for="(question, index) in $store.state.questions" :key="question.id" class="question-review">
            <div class="question-header">
              <span class="question-number">问题 {{ index + 1 }}</span>
              <span :class="['result-badge', isCorrect(index) ? 'correct' : 'incorrect']">
                {{ isCorrect(index) ? '✓ 正确' : '✗ 错误' }}
              </span>
            </div>
            <p class="question-text">{{ question.question }}</p>
            <div class="answer-details">
              <p v-if="question.type === 'choice'">
                <strong>你的答案:</strong> {{ $store.state.userAnswers[index] || '未答' }}<br>
                <strong>正确答案:</strong> {{ question.correctAnswer }}
              </p>
              <p v-else-if="question.type === 'judgment'">
                <strong>你的答案:</strong> {{ $store.state.userAnswers[index] === true ? '正确' : '错误' }}<br>
                <strong>正确答案:</strong> {{ question.correctAnswer === true ? '正确' : '错误' }}
              </p>
              <p v-else>
                <strong>你的答案:</strong> {{ $store.state.userAnswers[index] || '未答' }}<br>
                <strong>正确答案:</strong> {{ question.correctAnswer }}
              </p>
              <p class="explanation">{{ question.explanation }}</p>
            </div>
          </div>
        </div>
        
        <button @click="restartQuiz" class="restart-button">重新开始</button>
      </div>
      
      <div v-else class="question-container">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: $store.getters.progress + '%' }"></div>
        </div>
        <p class="question-counter">问题 {{ $store.state.currentQuestionIndex + 1 }}/{{ $store.state.questions.length }}</p>
        
        <div v-if="$store.getters.currentQuestion" class="current-question">
          <h3>{{ $store.getters.currentQuestion.question }}</h3>
          
          <!-- 判断题 -->
          <div v-if="$store.getters.currentQuestion.type === 'judgment'" class="judgment-question">
            <button 
              @click="submitAnswer(true)" 
              :class="['judgment-btn', $store.state.userAnswers[$store.state.currentQuestionIndex] === true ? 'selected' : '']"
              :disabled="$store.state.feedbackShown"
            >
              正确
            </button>
            <button 
              @click="submitAnswer(false)" 
              :class="['judgment-btn', $store.state.userAnswers[$store.state.currentQuestionIndex] === false ? 'selected' : '']"
              :disabled="$store.state.feedbackShown"
            >
              错误
            </button>
          </div>
          
          <!-- 选择题 -->
          <div v-else-if="$store.getters.currentQuestion.type === 'choice'" class="choice-question">
            <div 
              v-for="option in $store.getters.currentQuestion.options" 
              :key="option"
              @click="submitAnswer(option)"
              :class="['option', $store.state.userAnswers[$store.state.currentQuestionIndex] === option ? 'selected' : '']"
              :disabled="$store.state.feedbackShown"
            >
              {{ option }}
            </div>
          </div>
          
          <!-- 简答题 -->
          <div v-else-if="$store.getters.currentQuestion.type === 'simple_answer'" class="simple-answer-question">
            <input 
              type="text" 
              v-model="answerInput" 
              placeholder="请输入你的答案"
              :disabled="$store.state.feedbackShown"
            />
            <button @click="submitAnswer(answerInput)" :disabled="$store.state.feedbackShown || !answerInput">
              提交
            </button>
          </div>
          
          <!-- 答案反馈 -->
          <div v-if="$store.state.feedbackShown" class="feedback">
            <div class="feedback-header" :class="isCurrentAnswerCorrect ? 'correct' : 'incorrect'">
              {{ isCurrentAnswerCorrect ? '✓ 答对了!' : '✗ 答错了!' }}
            </div>
            <p class="feedback-text">
              {{ $store.getters.currentQuestion.explanation }}
            </p>
            <button @click="nextQuestion" class="next-button">
              {{ isLastQuestion ? '查看结果' : '下一题' }}
            </button>
          </div>
        </div>
      </div>
    </main>
    
    <footer>
      <p>© 2050 AI知识竞答 | 版权所有</p>
    </footer>
  </div>

  <!-- 添加隐藏的音频播放器组件 -->
  <audio ref="questionAudio" style="display:none"></audio>
  <audio ref="feedbackAudio" style="display:none"></audio>
  <audio ref="testAudio" style="display:none"></audio>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      answerInput: '',
      testAudioData: 'data:audio/mp3;base64,SUQzAwAAAAAAIlRJVDIAAAAZAAAAaHR0cDovL3d3dy55b3V0dWJlLmNvbS9FAAAAA1RBRwAAABgAAABoAHQAdABwADoALwAvAHcAdwB3AC4AeQBvAHUAdAB1AGIAZQAuAGMAbwBtAC8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
    }
  },
  computed: {
    audioEnabled() {
      return this.$store.state.audioEnabled;
    },
    isCurrentAnswerCorrect() {
      const currentQuestion = this.$store.getters.currentQuestion;
      if (!currentQuestion) return false;
      
      const questionId = currentQuestion.id;
      const feedback = this.$store.getters.getFeedback(questionId);
      
      return feedback && feedback.isCorrect;
    },
    isLastQuestion() {
      return this.$store.getters.isLastQuestion;
    }
  },
  methods: {
    startQuiz() {
      // 重置并获取题目
      this.$store.commit('RESET_QUIZ');
      this.$store.dispatch('fetchQuestions').then(() => {
        // 获取题目成功后启动测验
        this.$store.commit('START_QUIZ');
        console.log('测验已启动，quizStarted =', this.$store.state.quizStarted);
      });
    },
    
    restartQuiz() {
      // 重置并获取题目
      this.$store.commit('RESET_QUIZ');
      this.$store.dispatch('fetchQuestions').then(() => {
        // 获取题目成功后启动测验
        this.$store.commit('START_QUIZ');
      });
    },
    
    submitAnswer(answer) {
      if (this.$store.state.feedbackShown) return;
      
      // 使用store中的方法
      const currentQuestion = this.$store.getters.currentQuestion;
      if (currentQuestion) {
        try {
          // 设置用户答案
          this.$store.commit('SET_USER_ANSWER', { 
            questionId: currentQuestion.id, 
            answer: answer 
          });
          
          // 显示反馈
          this.$store.commit('SET_FEEDBACK_SHOWN', true);
          
          // 获取答案反馈
          this.$store.dispatch('submitAnswer', {
            questionId: currentQuestion.id,
            answer: answer,
            questionType: currentQuestion.type,
            question: currentQuestion.question,
            correctAnswer: currentQuestion.correctAnswer
          });
          
          // 延迟一段时间后尝试播放反馈音频
          setTimeout(() => {
            this.playFeedbackAudio(currentQuestion.id);
          }, 1000); // 延迟1秒
        } catch (error) {
          console.error('提交答案时出错:', error);
        }
      }
    },
    
    // 播放问题音频
    playQuestionAudio() {
      const currentQuestion = this.$store.getters.currentQuestion;
      if (currentQuestion && this.$store.state.audioEnabled) {
        console.log('尝试播放问题音频:', currentQuestion.id);
        
        if (!currentQuestion.audio) {
          console.warn('问题没有音频数据');
          return;
        }
        
        // 如果TTS服务有错误，显示错误消息但不影响应用继续使用
        if (currentQuestion.audio.error) {
          console.warn('TTS服务错误:', currentQuestion.audio.error);
          return;
        }
        
        // 如果音频数据为空，跳过播放
        if (!currentQuestion.audio.audio_base64 && !currentQuestion.audio.file_path) {
          console.warn('音频数据为空');
          return;
        }
        
        const audioElement = this.$refs.questionAudio;
        if (audioElement) {
          try {
            if (currentQuestion.audio.audio_base64) {
              console.log('使用base64音频数据');
              audioElement.src = `data:audio/mp3;base64,${currentQuestion.audio.audio_base64}`;
            } else if (currentQuestion.audio.file_path) {
              console.log('使用音频文件路径:', currentQuestion.audio.file_path);
              // 确保路径以正确的形式使用
              let audioPath = currentQuestion.audio.file_path;
              if (!audioPath.startsWith('http') && !audioPath.startsWith('/api')) {
                audioPath = `/api${audioPath}`;
              }
              audioElement.src = audioPath;
            } else {
              console.warn('问题音频数据格式不正确');
              return;
            }
            
            // 监听加载事件
            audioElement.onloadeddata = () => {
              console.log('音频数据已加载，准备播放');
            };
            
            // 监听错误事件
            audioElement.onerror = (e) => {
              console.error('音频加载失败:', e);
            };
            
            // 监听播放事件
            audioElement.onplay = () => {
              console.log('音频开始播放');
            };
            
            // 尝试播放
            const playPromise = audioElement.play();
            if (playPromise !== undefined) {
              playPromise
                .then(() => {
                  console.log('音频播放成功');
                })
                .catch(e => {
                  console.error('无法播放问题音频:', e);
                });
            }
          } catch (error) {
            console.error('播放问题音频时出错:', error);
          }
        }
      }
    },
    
    // 播放反馈音频
    playFeedbackAudio(questionId) {
      console.log('尝试播放反馈音频:', questionId);
      const feedback = this.$store.getters.getFeedback(questionId);
      
      if (!feedback) {
        console.warn('未找到问题的反馈');
        return;
      }
      
      console.log('找到的反馈:', feedback);
      
      if (feedback && feedback.audio && this.$store.state.audioEnabled) {
        // 如果TTS服务有错误，显示错误消息但不影响应用继续使用
        if (feedback.audio.error) {
          console.warn('TTS服务错误:', feedback.audio.error);
          return;
        }
        
        // 如果音频数据为空，跳过播放
        if (!feedback.audio.audio_base64 && !feedback.audio.file_path) {
          console.warn('音频数据为空');
          return;
        }
        
        const audioElement = this.$refs.feedbackAudio;
        if (audioElement) {
          try {
            if (feedback.audio.audio_base64) {
              console.log('使用base64音频数据');
              audioElement.src = `data:audio/mp3;base64,${feedback.audio.audio_base64}`;
            } else if (feedback.audio.file_path) {
              console.log('使用音频文件路径:', feedback.audio.file_path);
              // 确保路径以正确的形式使用
              let audioPath = feedback.audio.file_path;
              if (!audioPath.startsWith('http') && !audioPath.startsWith('/api')) {
                audioPath = `/api${audioPath}`;
              }
              audioElement.src = audioPath;
            } else {
              console.warn('反馈音频数据格式不正确');
              return;
            }
            
            // 监听加载事件
            audioElement.onloadeddata = () => {
              console.log('反馈音频数据已加载，准备播放');
            };
            
            // 监听错误事件
            audioElement.onerror = (e) => {
              console.error('反馈音频加载失败:', e);
            };
            
            // 监听播放事件
            audioElement.onplay = () => {
              console.log('反馈音频开始播放');
            };
            
            // 尝试播放
            const playPromise = audioElement.play();
            if (playPromise !== undefined) {
              playPromise
                .then(() => {
                  console.log('反馈音频播放成功');
                })
                .catch(e => {
                  console.error('无法播放反馈音频:', e);
                });
            }
          } catch (error) {
            console.error('播放反馈音频时出错:', error);
          }
        }
      } else {
        console.warn('反馈没有音频数据或音频已禁用');
      }
    },
    
    nextQuestion() {
      // 隐藏当前反馈
      this.$store.commit('SET_FEEDBACK_SHOWN', false);
      this.answerInput = '';
      
      if (this.isLastQuestion) {
        this.$store.commit('SET_QUIZ_COMPLETED', true);
        this.$store.dispatch('getFinalScore');
      } else {
        this.$store.commit('NEXT_QUESTION');
        // 在切换到下一题后播放问题音频
        this.$nextTick(() => {
          this.playQuestionAudio();
        });
      }
    },
    retryFetchQuestions() {
      this.$store.dispatch('fetchQuestions')
    },
    isCorrect(index) {
      const question = this.$store.state.questions[index]
      const userAnswer = this.$store.state.userAnswers[index]
      
      if (!question || userAnswer === undefined) return false
      
      if (question.type === 'simple_answer') {
        return userAnswer.trim().toLowerCase() === question.correctAnswer.trim().toLowerCase()
      }
      
      return userAnswer === question.correctAnswer
    },
    
    toggleAudio() {
      this.$store.commit('toggleAudio');
    },
    
    testAudio() {
      console.log('测试音频播放...');
      const audioElement = this.$refs.testAudio;
      if (audioElement) {
        audioElement.src = this.testAudioData;
        audioElement.onloadeddata = () => {
          console.log('测试音频已加载');
        };
        audioElement.onplay = () => {
          console.log('测试音频开始播放');
        };
        audioElement.onerror = (e) => {
          console.error('测试音频加载失败:', e);
        };
        
        const playPromise = audioElement.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              console.log('测试音频播放成功');
              alert('如果您能听到声音，说明音频功能正常！');
            })
            .catch(e => {
              console.error('无法播放测试音频:', e);
              alert('无法播放音频: ' + e.message);
            });
        }
      }
    }
  },
  watch: {
    // 监听当前问题索引变化，播放问题音频
    '$store.state.currentQuestionIndex': function() {
      this.$nextTick(() => {
        this.playQuestionAudio();
      });
    }
  },
  mounted() {
    // 初始化时播放第一个问题的音频
    this.$nextTick(() => {
      if (this.$store.state.quizStarted && this.$store.getters.currentQuestion) {
        this.playQuestionAudio();
      }
    });
  },
  created() {
    this.$store.dispatch('fetchQuestions')
  }
}
</script>

<style>
:root {
  --primary-color: #3498db;
  --secondary-color: #2c3e50;
  --success-color: #2ecc71;
  --danger-color: #e74c3c;
  --background-color: #f5f7fa;
  --card-color: #ffffff;
  --text-color: #333333;
  --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  --border-radius: 8px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background-color: var(--background-color);
  color: var(--text-color);
  line-height: 1.6;
}

.app-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

header h1 {
  color: var(--primary-color);
  font-size: 28px;
}

.audio-toggle, .test-audio-btn {
  background: none;
  border: 1px solid var(--primary-color);
  padding: 5px 10px;
  border-radius: var(--border-radius);
  margin-left: 10px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s;
}

.audio-toggle:hover, .test-audio-btn:hover {
  background-color: rgba(52, 152, 219, 0.1);
}

.test-audio-btn {
  font-size: 14px;
  background-color: var(--primary-color);
  color: white;
}

main {
  flex: 1;
}

.error-message {
  background-color: rgba(231, 76, 60, 0.1);
  padding: 15px;
  border-radius: var(--border-radius);
  margin-bottom: 20px;
  color: var(--danger-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.error-message button {
  background-color: var(--danger-color);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: var(--border-radius);
  cursor: pointer;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.welcome-screen, .results-screen {
  background-color: var(--card-color);
  padding: 30px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
  text-align: center;
}

.welcome-screen h2, .results-screen h2 {
  margin-bottom: 20px;
  color: var(--secondary-color);
}

.welcome-screen p {
  margin-bottom: 30px;
  font-size: 18px;
}

.note {
  margin-bottom: 30px;
  font-size: 14px;
  color: #666;
}

.start-button, .restart-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: var(--border-radius);
  font-size: 18px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.start-button:hover, .restart-button:hover {
  background-color: #2980b9;
}

.question-container {
  background-color: var(--card-color);
  padding: 30px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
}

.progress-bar {
  height: 8px;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  transition: width 0.3s ease;
}

.question-counter {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
  text-align: right;
}

.current-question h3 {
  font-size: 22px;
  margin-bottom: 25px;
  line-height: 1.4;
}

.judgment-question {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 30px;
}

.judgment-btn {
  padding: 12px 30px;
  border: 2px solid var(--primary-color);
  border-radius: var(--border-radius);
  background-color: white;
  color: var(--primary-color);
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}

.judgment-btn:hover:not(:disabled) {
  background-color: rgba(52, 152, 219, 0.1);
}

.judgment-btn.selected {
  background-color: var(--primary-color);
  color: white;
}

.choice-question {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 30px;
}

.option {
  padding: 12px 20px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s;
}

.option:hover:not(:disabled) {
  border-color: var(--primary-color);
  background-color: rgba(52, 152, 219, 0.05);
}

.option.selected {
  border-color: var(--primary-color);
  background-color: var(--primary-color);
  color: white;
}

.simple-answer-question {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

.simple-answer-question input {
  flex: 1;
  padding: 12px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: var(--border-radius);
  font-size: 16px;
}

.simple-answer-question input:focus {
  border-color: var(--primary-color);
  outline: none;
}

.simple-answer-question button {
  padding: 0 20px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
}

.simple-answer-question button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.feedback {
  margin-top: 30px;
  padding: 20px;
  border-radius: var(--border-radius);
  background-color: rgba(0, 0, 0, 0.05);
}

.feedback-header {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 15px;
}

.feedback-header.correct {
  color: var(--success-color);
}

.feedback-header.incorrect {
  color: var(--danger-color);
}

.feedback-text {
  margin-bottom: 20px;
  line-height: 1.5;
}

.next-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: 16px;
}

.score-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 30px 0;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: var(--primary-color);
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 15px;
}

.score-text {
  color: white;
  font-size: 32px;
  font-weight: bold;
}

.answers-review {
  margin: 30px 0;
  text-align: left;
}

.answers-review h3 {
  margin-bottom: 20px;
  font-size: 20px;
  text-align: center;
}

.question-review {
  margin-bottom: 25px;
  padding: 15px;
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: var(--border-radius);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.question-number {
  font-weight: bold;
}

.result-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
}

.result-badge.correct {
  background-color: rgba(46, 204, 113, 0.2);
  color: var(--success-color);
}

.result-badge.incorrect {
  background-color: rgba(231, 76, 60, 0.2);
  color: var(--danger-color);
}

.question-text {
  margin-bottom: 12px;
  font-weight: 500;
}

.answer-details {
  font-size: 14px;
}

.explanation {
  margin-top: 10px;
  font-style: italic;
  color: #666;
}

footer {
  margin-top: 40px;
  text-align: center;
  font-size: 14px;
  color: #666;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style> 