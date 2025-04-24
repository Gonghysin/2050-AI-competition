<template>
  <div class="emoji-container">
    <div :class="['emoji-animation', status]">
      {{ currentEmoji }}
    </div>
    <div class="emoji-caption" v-if="showCaption">{{ statusCaption }}</div>
  </div>
</template>

<script>
export default {
  name: 'EmojiAnimation',
  props: {
    status: {
      type: String,
      default: 'idle',
      validator: (value) => ['idle', 'thinking', 'quiz', 'happy', 'surprised', 'correct', 'wrong'].includes(value)
    },
    showCaption: {
      type: Boolean,
      default: true
    }
  },
  computed: {
    currentEmoji() {
      const emojis = {
        idle: '🐸',       // 青蛙默认状态
        thinking: '🤔',   // 思考中
        quiz: '📝',       // 出题模式
        happy: '😊',      // 开心
        surprised: '😲',  // 惊讶
        correct: '👍',    // 答对了
        wrong: '👎'       // 答错了
      };
      
      return emojis[this.status] || emojis.idle;
    },
    statusCaption() {
      const captions = {
        idle: '邪恶青蛙博士正在聆听...',
        thinking: '邪恶青蛙博士正在思考...',
        quiz: '邪恶青蛙博士正在出题...',
        happy: '邪恶青蛙博士很开心！',
        surprised: '邪恶青蛙博士感到惊讶！',
        correct: '回答正确！',
        wrong: '回答错误！'
      };
      
      return captions[this.status] || captions.idle;
    }
  }
}
</script>

<style scoped lang="scss">
.emoji-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
  min-height: 160px;
}

.emoji-animation {
  display: inline-block;
  font-size: 6rem;
  margin-bottom: 10px;
  text-shadow: 0 2px 10px rgba(0,0,0,0.1);
  
  &.idle {
    animation: float 3s infinite ease-in-out;
  }
  
  &.thinking {
    animation: pulse 1.5s infinite alternate;
  }
  
  &.quiz {
    animation: bounce 2s infinite;
  }
  
  &.happy {
    animation: tada 1.5s infinite;
  }
  
  &.surprised {
    animation: wobble 1.5s;
  }
  
  &.correct {
    animation: rubberBand 1s;
  }
  
  &.wrong {
    animation: shake 0.8s;
  }
}

.emoji-caption {
  font-size: 0.9rem;
  color: #777;
  text-align: center;
}

@keyframes float {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
  100% {
    transform: translateY(0px);
  }
}

@keyframes tada {
  0% {transform: scale(1);}
  10%, 20% {transform: scale(0.9) rotate(-3deg);}
  30%, 50%, 70%, 90% {transform: scale(1.1) rotate(3deg);}
  40%, 60%, 80% {transform: scale(1.1) rotate(-3deg);}
  100% {transform: scale(1) rotate(0);}
}

@keyframes wobble {
  0% {transform: translateX(0%);}
  15% {transform: translateX(-25%) rotate(-5deg);}
  30% {transform: translateX(20%) rotate(3deg);}
  45% {transform: translateX(-15%) rotate(-3deg);}
  60% {transform: translateX(10%) rotate(2deg);}
  75% {transform: translateX(-5%) rotate(-1deg);}
  100% {transform: translateX(0%);}
}

@keyframes rubberBand {
  0% {transform: scale(1);}
  30% {transform: scaleX(1.25) scaleY(0.75);}
  40% {transform: scaleX(0.75) scaleY(1.25);}
  50% {transform: scaleX(1.15) scaleY(0.85);}
  65% {transform: scaleX(0.95) scaleY(1.05);}
  75% {transform: scaleX(1.05) scaleY(0.95);}
  100% {transform: scale(1);}
}
</style> 