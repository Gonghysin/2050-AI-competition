<template>
  <div class="emoji-container">
    <div :class="['emoji-animation', status]">
      {{ currentEmoji }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'EmojiAnimation',
  props: {
    status: {
      type: String,
      default: 'idle',
      validator: (value) => ['idle', 'thinking', 'quiz', 'happy', 'surprised'].includes(value)
    }
  },
  computed: {
    currentEmoji() {
      const emojis = {
        idle: '🐸',       // 青蛙默认状态
        thinking: '🤔',   // 思考中
        quiz: '📝',       // 出题模式
        happy: '😊',      // 开心
        surprised: '😲'   // 惊讶
      };
      
      return emojis[this.status] || emojis.idle;
    }
  }
}
</script>

<style scoped lang="scss">
.emoji-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  min-height: 120px;
}

.emoji-animation {
  display: inline-block;
  font-size: 5rem;
  text-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
</style> 