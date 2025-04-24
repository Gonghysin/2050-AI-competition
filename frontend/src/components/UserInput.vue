<template>
  <div class="user-input-container">
    <input
      type="text"
      v-model="message"
      @keyup.enter="handleSubmit"
      :disabled="isLoading"
      :placeholder="challengeMode ? '请输入您的答案...' : '请输入消息...'"
      class="input-field"
    />
    <button 
      @click="handleSubmit" 
      :disabled="isLoading"
      class="send-button"
    >
      {{ isLoading ? '请稍等...' : (challengeMode ? '提交' : '发送') }}
    </button>
  </div>
</template>

<script>
export default {
  name: 'UserInput',
  props: {
    isLoading: {
      type: Boolean,
      default: false
    },
    challengeMode: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      message: ''
    };
  },
  watch: {
    isLoading(newVal) {
      console.log(`[UserInput] 加载状态: ${newVal ? '正在加载' : '加载完成'}`);
    }
  },
  methods: {
    handleSubmit() {
      if (this.isLoading || !this.message.trim()) return;
      
      if (this.challengeMode) {
        console.log(`[UserInput] 提交答案: ${this.message}`);
        this.$emit('submit-answer', this.message);
      } else {
        console.log(`[UserInput] 发送消息: ${this.message.substring(0, 30)}${this.message.length > 30 ? '...' : ''}`);
        this.$emit('send-message', this.message);
      }
      
      this.message = '';
    }
  },
  created() {
    console.log('[UserInput] 组件创建');
  }
};
</script>

<style scoped>
.user-input-container {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 30px;
  padding: 15px;
  box-sizing: border-box;
  position: relative;
  bottom: 0;
}

.input-field {
  width: 70%;
  height: 50px;
  border: none;
  border-radius: 25px;
  padding: 0 20px;
  font-size: 16px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  outline: none;
  transition: all 0.3s;
}

.input-field:focus {
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.input-field:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  margin-left: 10px;
  width: 100px;
  height: 50px;
  border: none;
  border-radius: 25px;
  background-color: #4CAF50;
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.send-button:hover:not(:disabled) {
  background-color: #45a049;
}

.send-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style> 