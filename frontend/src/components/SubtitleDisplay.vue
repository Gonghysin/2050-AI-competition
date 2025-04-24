<template>
  <div class="subtitle-container">
    <div class="subtitle-text" v-html="formattedText"></div>
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
  computed: {
    formattedText() {
      if (!this.text) return '等待输入...';
      
      // 处理文本格式
      let formatted = this.text
        // 在数字列表前添加换行
        .replace(/(\d+[\.\)、])\s*/g, '<br>$1 ')
        // 在中文句号、问号、感叹号后添加换行
        .replace(/([。！？\?\.!])\s*/g, '$1<br>')
        // 处理特殊的分隔符和标点
        .replace(/[:：]\s*/g, '：<br>')
        // 处理段落标识符
        .replace(/^(第.*?[章节部篇].*?)$/mg, '<br><strong>$1</strong><br>')
        // 处理数学题目中的问题和解答
        .replace(/(问题[:：]|题目[:：]|解[:：]|答[:：])/g, '<br><strong>$1</strong> ')
        // 将连续的多个换行符替换为最多两个
        .replace(/<br>\s*<br>\s*<br>/g, '<br><br>');
      
      return formatted;
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
  line-height: 1.8;
  color: #333;
  text-align: left;
  width: 100%;
  max-width: 700px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 25px;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  animation: fadeIn 0.5s;
  white-space: pre-line;
}

.subtitle-text strong {
  font-weight: bold;
  color: #2c3e50;
}

.subtitle-text br {
  display: block;
  content: "";
  margin-top: 10px;
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