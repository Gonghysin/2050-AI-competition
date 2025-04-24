# AI对话助手前端

这是AI对话助手的前端部分，基于Vue.js构建。

## 主要功能

- 与AI进行对话交流
- 展示AI不同状态的emoji表情
- 显示AI回复字幕
- 播放AI回复的语音

## 项目设置

### 安装依赖
```
npm install
```

### 启动开发服务器
```
npm run serve
```

### 构建生产版本
```
npm run build
```

## 组件结构

- **AIEmoji**: 展示AI不同状态的emoji表情
- **SubtitleDisplay**: 显示AI回复字幕
- **UserInput**: 用户输入区域

## 与后端通信

前端通过以下API与后端通信：

- `/api/chat`: 普通对话API
- `/api/chat/stream`: 流式对话API

详情请参考后端API文档。 