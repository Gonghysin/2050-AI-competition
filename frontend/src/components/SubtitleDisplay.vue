<template>
  <div class="subtitle-container">
    <div class="subtitle-text">
      {{ text || '等待输入...' }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubtitleDisplay',
  props: {
    text: {
      type: String,
      default: ''
    }
  },
  watch: {
    text(newVal, oldVal) {
      if (newVal !== oldVal) {
        console.log(`[SubtitleDisplay] 文本更新: ${newVal.length} 字符`);
      }
    }
  },
  created() {
    console.log('[SubtitleDisplay] 组件创建');
  }
};
</script>

<style scoped>
.subtitle-container {
  width: 100%;
  min-height: 120px;
  margin: 20px 0;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 15px;
  box-sizing: border-box;
}

.subtitle-text {
  font-size: 22px;
  line-height: 1.6;
  color: #333;
  text-align: center;
  width: 100%;
  max-width: 700px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style> 