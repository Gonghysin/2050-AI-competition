<template>
  <div class="ai-emoji-container">
    <div class="emoji" :class="status">
      <div v-if="status === 'idle'" class="emoji-group">
        <span class="emoji-item">🐸</span>
        <span class="emoji-item">🙌</span>
        <span class="emoji-item">😭</span>
      </div>
      <div v-else-if="status === 'thinking'" class="emoji-group">
        <span class="emoji-item">🐸</span>
        <span class="emoji-item animation-delay-1">✍️</span>
        <span class="emoji-item animation-delay-2">✍️</span>
        <div class="thinking-text">思考中...</div>
      </div>
      <div v-else-if="status === 'speaking'" class="emoji-group">
        <span class="emoji-item animation-hand-left">🫲</span>
        <span class="emoji-item">🐸</span>
        <span class="emoji-item animation-hand-right">🫱</span>
      </div>
      <div v-else-if="status === 'error'" class="emoji-group">
        <span class="emoji-item">🐸</span>
        <span class="emoji-item animation-rotate">🤣</span>
        <span class="emoji-item animation-pointing">👉</span>
      </div>
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
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  border-radius: 50%;
  background-color: #e9f5ff;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
}

.emoji-group {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.emoji-item {
  font-size: 60px;
  margin: 0 5px;
  display: inline-block;
}

.thinking-text {
  position: absolute;
  bottom: 20px;
  font-size: 24px;
  color: #333;
  font-weight: bold;
}

.emoji.idle {
  background-color: #e9f5ff;
}

.emoji.idle .emoji-item:nth-child(2) {
  animation: float 2s ease-in-out infinite;
}

.emoji.thinking {
  background-color: #fff5e9;
  animation: pulse 1.5s infinite;
}

.emoji.thinking .emoji-item {
  animation: thinking 0.8s infinite;
}

.animation-delay-1 {
  animation-delay: 0.2s !important;
}

.animation-delay-2 {
  animation-delay: 0.4s !important;
}

.emoji.speaking {
  background-color: #e9fff0;
}

.emoji.speaking .emoji-item:nth-child(2) {
  animation: bounce 0.8s infinite;
  font-size: 70px;
}

.animation-hand-left {
  animation: handLeft 1s infinite;
  margin-right: -8px;
}

.animation-hand-right {
  animation: handRight 1s infinite;
  margin-left: -8px;
}

.emoji.error {
  background-color: #ffe9e9;
}

.animation-rotate {
  animation: rotate 2s infinite;
}

.animation-pointing {
  animation: pointing 1s infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
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

@keyframes thinking {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
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

@keyframes handLeft {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-5px);
  }
}

@keyframes handRight {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(5px);
  }
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes pointing {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(8px);
  }
}
</style> 