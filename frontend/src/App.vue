<template>
  <div class="app-container">
    <div class="chat-container">
      <!-- AI Emoji组件 -->
      <AIEmoji :status="aiStatus" />
      
      <!-- 字幕显示区域 -->
      <SubtitleDisplay :text="currentText" />
      
      <!-- 用户输入区域 -->
      <UserInput 
        @send-message="sendMessage" 
        :is-loading="aiStatus !== 'idle'" 
      />
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import AIEmoji from './components/AIEmoji.vue';
import SubtitleDisplay from './components/SubtitleDisplay.vue';
import UserInput from './components/UserInput.vue';

export default {
  name: 'App',
  components: {
    AIEmoji,
    SubtitleDisplay,
    UserInput
  },
  data() {
    return {
      aiStatus: 'idle', // idle, thinking, speaking, error
      currentText: '',
      sessionId: null,
      audioQueue: [],
      isAudioPlaying: false,
      eventSource: null,
      useStreamMode: true // 是否使用流式模式
    };
  },
  methods: {
    // 发送消息给AI
    async sendMessage(message) {
      if (!message.trim()) return;
      
      console.log(`[App] 发送消息: "${message.substring(0, 30)}${message.length > 30 ? '...' : ''}"`);
      
      // 重置状态
      this.currentText = '';
      this.audioQueue = [];
      this.aiStatus = 'thinking';
      console.log('[App] 状态变更为: thinking');
      
      if (this.eventSource) {
        console.log('[App] 关闭旧的EventSource连接');
        this.eventSource.close();
      }
      
      try {
        if (this.useStreamMode) {
          console.log('[App] 使用流式模式处理消息');
          // 使用流式模式
          this.handleStreamMode(message);
        } else {
          console.log('[App] 使用普通模式处理消息');
          // 使用普通模式
          await this.handleNormalMode(message);
        }
      } catch (error) {
        console.error('[App] 发送消息出错:', error);
        this.aiStatus = 'error';
        console.log('[App] 状态变更为: error');
        this.currentText = '抱歉，出现了一些问题，请重试。';
      }
    },
    
    // 普通模式处理
    async handleNormalMode(message) {
      console.log('[App] 开始普通模式请求');
      const startTime = Date.now();
      
      try {
        const response = await axios.post('/api/chat', {
          message,
          session_id: this.sessionId
        });
        
        console.log(`[App] 普通模式请求完成, 耗时: ${Date.now() - startTime}ms`);
        console.log('[App] 响应数据:', response.data);
        
        const { message: aiMessage, audio_url, session_id } = response.data;
        
        // 保存会话ID
        this.sessionId = session_id;
        console.log(`[App] 会话ID: ${session_id}`);
        
        // 更新字幕
        this.currentText = aiMessage;
        console.log(`[App] 更新字幕: "${aiMessage.substring(0, 30)}${aiMessage.length > 30 ? '...' : ''}"`);
        
        // 播放音频
        this.aiStatus = 'speaking';
        console.log('[App] 状态变更为: speaking');
        console.log(`[App] 开始播放音频: ${audio_url}`);
        
        await this.playAudio(audio_url);
        
        console.log('[App] 音频播放完成');
        this.aiStatus = 'idle';
        console.log('[App] 状态变更为: idle');
      } catch (error) {
        console.error('[App] 普通模式请求出错:', error);
        throw error;
      }
    },
    
    // 流式模式处理
    handleStreamMode(message) {
      console.log('[App] 开始流式模式请求');
      const startTime = Date.now();
      
      // 设置请求数据
      const requestData = {
        message,
        session_id: this.sessionId
      };
      
      console.log('[App] 发送POST请求到流式API');
      // 先发送POST请求到流式API
      fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      })
      .then(response => response.json())
      .then(data => {
        console.log('[App] POST请求成功，获取request_id:', data.request_id);
        
        // 创建新的EventSource连接
        if (this.eventSource) {
          this.eventSource.close();
        }
        
        // 使用请求ID创建EventSource连接
        const url = `/api/chat/stream?request_id=${data.request_id}`;
        console.log(`[App] 创建EventSource连接: ${url}`);
        this.eventSource = new EventSource(url);
        
        // 监听事件
        this.eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('[App] 收到SSE事件:', data);
            
            // 处理文本更新
            if (data.text) {
              this.currentText += data.text;
              console.log(`[App] 更新字幕: 添加"${data.text}"`);
              
              if (this.aiStatus === 'thinking') {
                this.aiStatus = 'speaking';
                console.log('[App] 状态变更为: speaking');
              }
            }
            
            // 处理段落完成
            if (data.segment_done) {
              console.log(`[App] 段落完成, 音频URL: ${data.audio_url}`);
              console.log(`[App] 段落文本: "${data.segment_text.substring(0, 30)}${data.segment_text.length > 30 ? '...' : ''}"`);
              
              // 将音频添加到队列
              this.audioQueue.push(data.audio_url);
              console.log(`[App] 音频添加到队列, 当前队列长度: ${this.audioQueue.length}`);
              
              // 如果没有正在播放的音频，开始播放
              if (this.audioQueue.length === 1 && !this.isAudioPlaying) {
                console.log('[App] 开始播放音频队列');
                this.playNextAudio();
              }
            }
            
            // 处理生成完成
            if (data.done) {
              console.log('[App] 生成完成');
              
              // 保存会话ID
              this.sessionId = data.session_id;
              console.log(`[App] 会话ID: ${data.session_id}`);
              console.log(`[App] 共有段落数: ${data.segment_ids.length}`);
              
              // 关闭连接
              this.eventSource.close();
              this.eventSource = null;
              console.log('[App] 关闭EventSource连接');
              
              // 当所有音频播放完毕后，将状态改为idle
              if (this.audioQueue.length === 0 && !this.isAudioPlaying) {
                this.aiStatus = 'idle';
                console.log('[App] 状态变更为: idle');
              }
              
              console.log(`[App] 流式请求完成, 总耗时: ${Date.now() - startTime}ms`);
            }
            
            // 处理错误
            if (data.error) {
              console.error('[App] AI回复出错:', data.error);
              this.aiStatus = 'error';
              console.log('[App] 状态变更为: error');
              this.currentText = '抱歉，出现了一些问题，请重试。';
              this.eventSource.close();
              this.eventSource = null;
              console.log('[App] 关闭EventSource连接');
            }
          } catch (error) {
            console.error('[App] 解析SSE事件出错:', error, event.data);
          }
        };
        
        // 处理错误
        this.eventSource.onerror = (error) => {
          console.error('[App] EventSource错误:', error);
          this.aiStatus = 'error';
          console.log('[App] 状态变更为: error');
          this.currentText = '连接出错，请重试。';
          this.eventSource.close();
          this.eventSource = null;
          console.log('[App] 关闭EventSource连接');
        };
      })
      .catch(error => {
        console.error('[App] 流式请求出错:', error);
        this.aiStatus = 'error';
        console.log('[App] 状态变更为: error');
        this.currentText = '请求出错，请重试。';
      });
    },
    
    // 播放下一个音频
    async playNextAudio() {
      if (this.audioQueue.length === 0) {
        console.log('[App] 音频队列为空，播放完成');
        this.isAudioPlaying = false;
        if (this.eventSource === null) {
          this.aiStatus = 'idle';
          console.log('[App] 状态变更为: idle');
        }
        return;
      }
      
      this.isAudioPlaying = true;
      const audioUrl = this.audioQueue.shift();
      console.log(`[App] 播放音频: ${audioUrl}, 剩余队列长度: ${this.audioQueue.length}`);
      
      try {
        await this.playAudio(audioUrl);
        console.log('[App] 当前音频播放完成，继续播放下一个');
        // 播放完成后继续播放下一个
        this.playNextAudio();
      } catch (error) {
        console.error('[App] 音频播放出错:', error);
        this.isAudioPlaying = false;
        if (this.eventSource === null) {
          this.aiStatus = 'idle';
          console.log('[App] 状态变更为: idle');
        }
      }
    },
    
    // 播放单个音频文件
    playAudio(url) {
      console.log(`[App] 创建音频实例: ${url}`);
      return new Promise((resolve, reject) => {
        const audio = new Audio(url);
        
        audio.onloadeddata = () => {
          console.log(`[App] 音频数据加载完成，时长: ${audio.duration}秒`);
        };
        
        audio.onended = () => {
          console.log('[App] 音频播放结束');
          resolve();
        };
        
        audio.onerror = (error) => {
          console.error('[App] 音频加载错误:', error);
          reject(error);
        };
        
        console.log('[App] 开始播放音频');
        audio.play().catch(error => {
          console.error('[App] 播放音频失败:', error);
          reject(error);
        });
      });
    }
  },
  created() {
    console.log('[App] 组件创建，初始状态: idle');
  }
};
</script>

<style>
.app-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: #f8f9fa;
}

.chat-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 800px;
  height: 100%;
  padding: 20px;
  box-sizing: border-box;
}
</style> 