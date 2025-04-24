# AI对话网站API文档

## 基本信息

- 基础URL: `http://localhost:8000` (普通模式)
- 流式URL: `http://localhost:8001` (流式生成模式)

## API端点

### 1. 聊天接口 (普通模式)

**端点**: `/api/chat`  
**方法**: POST  
**描述**: 发送用户消息，获取AI回复和语音URL

**请求体**:
```json
{
  "session_id": "可选，会话ID，如果不提供则创建新会话",
  "message": "用户消息内容",
  "model": "可选，AI模型名称，默认为gpt-4o"
}
```

**成功响应**:
```json
{
  "session_id": "会话ID",
  "message": "AI回复的文本内容",
  "audio_url": "语音文件URL"
}
```

**错误响应**:
```json
{
  "error": "错误信息"
}
```

### 2. 流式聊天接口 (支持分段TTS)

**端点**: `/api/chat/stream`  
**方法**: POST  
**描述**: 发送用户消息，获取流式AI回复和分段TTS语音URL

**请求体**:
```json
{
  "session_id": "可选，会话ID，如果不提供则创建新会话",
  "message": "用户消息内容",
  "model": "可选，AI模型名称，默认为gpt-4o"
}
```

**响应**: Server-Sent Events (SSE)格式的流式响应，包含以下几种事件：

- 文本块更新:
```
data: {"text": "文本块内容", "done": false}
```

- 段落完成和TTS音频URL:
```
data: {
  "text": "最新文本块", 
  "done": false, 
  "segment_done": true,
  "segment_id": "段落ID",
  "segment_text": "完整段落文本",
  "audio_url": "段落语音文件URL"
}
```

- 生成完成信号:
```
data: {
  "text": "", 
  "done": true, 
  "session_id": "会话ID", 
  "segment_ids": ["段落1ID", "段落2ID", ...],
  "full_response": "完整回复文本"
}
```

- 错误信息:
```
data: {"error": "错误信息"}
```

### 3. 获取会话历史

**端点**: `/api/sessions/{session_id}`  
**方法**: GET  
**描述**: 获取特定会话的历史记录

**URL参数**:
- `session_id`: 会话ID

**成功响应**:
```json
{
  "session_id": "会话ID",
  "history": [
    {"role": "user", "content": "用户消息1"},
    {"role": "assistant", "content": "AI回复1"},
    {"role": "user", "content": "用户消息2"},
    {"role": "assistant", "content": "AI回复2"},
    ...
  ]
}
```

**错误响应**:
```json
{
  "error": "会话不存在"
}
```

### 4. 删除会话

**端点**: `/api/sessions/{session_id}`  
**方法**: DELETE  
**描述**: 删除特定会话

**URL参数**:
- `session_id`: 会话ID

**成功响应**:
```json
{
  "success": true,
  "message": "会话已删除"
}
```

### 5. 获取状态

**端点**: `/api/status`  
**方法**: GET  
**描述**: 获取AI状态信息

**成功响应**:
```json
{
  "status": "状态值"
}
```

### 6. 静态文件服务

**端点**: `/static/{filename}`  
**方法**: GET  
**描述**: 获取静态文件（如生成的语音文件）

## 使用示例

### 普通模式聊天流程

1. 发送消息到 `/api/chat`
2. 获取回复文本和音频URL
3. 显示文本，播放音频

### 流式模式聊天流程 (分段TTS)

1. 发送消息到 `/api/chat/stream`
2. 通过EventSource接收不同类型的事件:
   - 收到文本块事件时，实时更新显示文本
   - 收到段落完成事件时，播放该段落对应的音频
   - 收到生成完成事件时，更新状态（如修改AI状态emoji）

### 分段TTS的前端处理示例

```javascript
const eventSource = new EventSource('/api/chat/stream');
let currentText = '';
const audioQueue = []; // 音频队列

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // 处理文本更新
  if (data.text) {
    currentText += data.text;
    updateSubtitle(currentText);
  }
  
  // 处理段落完成
  if (data.segment_done) {
    // 将音频添加到队列
    audioQueue.push(data.audio_url);
    
    // 如果这是第一个音频且没有正在播放的内容，开始播放
    if (audioQueue.length === 1 && !isAudioPlaying()) {
      playNextAudio();
    }
  }
  
  // 处理生成完成
  if (data.done) {
    // 更新AI状态
    updateAIStatus('idle');
    eventSource.close();
  }
};

// 播放下一个音频
function playNextAudio() {
  if (audioQueue.length === 0) return;
  
  const audioUrl = audioQueue.shift();
  const audio = new Audio(audioUrl);
  
  // 当前音频播放完成后播放下一个
  audio.onended = () => {
    playNextAudio();
  };
  
  audio.play();
}
```

## 错误处理

所有API错误都会返回相应的HTTP状态码和错误信息。常见状态码：

- 200: 请求成功
- 400: 请求格式错误
- 404: 资源不存在
- 500: 服务器内部错误 