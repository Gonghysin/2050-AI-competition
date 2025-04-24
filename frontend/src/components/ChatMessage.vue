<template>
  <div :class="['message-container', role]">
    <div :class="['message-bubble', role]">
      <div class="message-content" v-html="formattedContent"></div>
      <div class="message-time">{{ formattedTime }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatMessage',
  props: {
    content: {
      type: String,
      required: true
    },
    role: {
      type: String,
      default: 'user',
      validator: (value) => ['user', 'agent'].includes(value)
    },
    timestamp: {
      type: String,
      default: () => new Date().toISOString()
    }
  },
  computed: {
    formattedContent() {
      // 将换行符转换为<br>标签
      return this.content.replace(/\n/g, '<br>');
    },
    formattedTime() {
      try {
        const date = new Date(this.timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } catch (error) {
        return '';
      }
    }
  }
}
</script>

<style scoped lang="scss">
.message-container {
  display: flex;
  margin-bottom: 16px;
  width: 100%;
  
  &.user {
    justify-content: flex-end;
  }
  
  &.agent {
    justify-content: flex-start;
  }
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  max-width: 80%;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  position: relative;
  
  &.user {
    background-color: #e3f2fd;
    border-bottom-right-radius: 4px;
  }
  
  &.agent {
    background-color: #f1f8e9;
    border-bottom-left-radius: 4px;
  }
}

.message-content {
  word-break: break-word;
  line-height: 1.5;
}

.message-time {
  font-size: 12px;
  color: #9e9e9e;
  text-align: right;
  margin-top: 4px;
}
</style> 