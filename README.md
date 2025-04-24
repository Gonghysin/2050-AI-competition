# AI对话表情助手

一个集成AI对话、TTS语音和表情展示的交互式网站。

## 项目概述

本项目是一个交互式AI对话网站，具有以下主要特点：

1. **中央emoji表情**：根据AI不同状态（思考中、回复中、空闲、错误）展示不同的emoji表情
2. **字幕式回复**：AI回复不使用聊天气泡，而是以字幕形式在emoji下方显示
3. **语音播放**：将AI回复转换为语音并自动播放
4. **流式交互**：支持流式文本生成和分段TTS语音生成

## 项目结构

- `backend/`: 后端代码
  - `app.py`: 普通模式API服务
  - `stream_app.py`: 流式模式API服务
  - `run.py`: 启动脚本
  - `API_DOCS.md`: API文档
  - `static/`: 生成的语音文件存储目录
  
- `frontend/`: 前端代码
  - `src/`: 源代码目录
    - `components/`: Vue组件
      - `AIEmoji.vue`: AI表情组件
      - `SubtitleDisplay.vue`: 字幕显示组件
      - `UserInput.vue`: 用户输入组件
    - `App.vue`: 主应用组件
    - `main.js`: 入口文件
  
- `my_code_repository/`: 外部代码库
  - `AI_helper/`: AI助手代码
    - `yunwu_helper.py`: 云雾AI接口

- `src/`: 原项目源代码
  - `tts_helper.py`: TTS助手代码

## 技术栈

- **后端**: Python, Flask
- **前端**: Vue.js, Axios
- **AI接口**: 云雾AI API
- **TTS服务**: 方舟豆包TTS

## 安装与运行

### 安装依赖

```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 运行后端

```bash
cd backend
python run.py --mode both  # 同时启动普通模式和流式模式
# 或者
python run.py --mode normal  # 仅启动普通模式
python run.py --mode stream  # 仅启动流式模式
```

### 运行前端

```bash
cd frontend
npm run serve
```

## 使用说明

1. 打开浏览器访问 `http://localhost:8080`
2. 在输入框中输入消息并发送
3. 观察AI状态的emoji变化
4. 查看AI回复的字幕并聆听语音

## 主要功能

### AI状态表情

- **空闲状态**: 😊
- **思考中**: 🤔
- **回复中**: 🗣️
- **错误状态**: 😅

### 对话模式

- **普通模式**: 等待完整回复后生成语音
- **流式模式**: 流式生成文本，分段生成语音

## API文档

详细的API文档请参考 `backend/API_DOCS.md`
