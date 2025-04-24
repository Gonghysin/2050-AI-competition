<template>
  <div class="ai-emoji-container">
    <div class="emoji" :class="status">
      <span v-if="status === 'idle'">😊</span>
      <span v-else-if="status === 'thinking'">🤔</span>
      <span v-else-if="status === 'speaking'">🗣️</span>
      <span v-else-if="status === 'error'">😅</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AIEmoji',
  props: {
    status: {
      type: String,
      default: 'idle',
      validator: (value) => ['idle', 'thinking', 'speaking', 'error'].includes(value)
    }
  },
  watch: {
    status(newVal, oldVal) {
      console.log(`[AIEmoji] 状态变更: ${oldVal} -> ${newVal}`);
    }
  },
  created() {
    console.log(`[AIEmoji] 组件创建，初始状态: ${this.status}`);
  }
};
</script>

<style scoped>
.ai-emoji-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  width: 200px;
  margin: 20px 0;
}

.emoji {
  font-size: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  border-radius: 50%;
  background-color: #e9f5ff;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.emoji.idle {
  background-color: #e9f5ff;
}

.emoji.thinking {
  background-color: #fff5e9;
  animation: pulse 1.5s infinite;
}

.emoji.speaking {
  background-color: #e9fff0;
  animation: bounce 0.8s infinite;
}

.emoji.error {
  background-color: #ffe9e9;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}
</style> 