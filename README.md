# -_-

AI助手moudel：
./my_code_repository/AI_helper/yunwu_helper.py

后端：python

前段：vue

TTS：方舟豆包TTS。调用方法:
1. 接口说明
接口地址为 https://openspeech.bytedance.com/api/v1/tts

2. 身份认证
认证方式采用 Bearer Token.

1)需要在请求的 Header 中填入"Authorization":"Bearer;${token}"

注意

Bearer和token使用分号 ; 分隔，替换时请勿保留${}
发送参数文档：https://www.volcengine.com/docs/6561/79823
返回参数文档：https://www.volcengine.com/docs/6561/79823

APPID：5171308068
access token：DMwm_fkqA4lHn9-WhsxnRpbERJRRLSkH
voice type：BV119_streaming

TTS模块：./src/test_tts.py
题库：./src/data/evil_frog_quiz_database.json

123
我是谁

---

我理解您的需求是创建一个网站，实现用户与AI对话的功能，主要特点包括：

1. **界面设计**：
   - 屏幕中央显示表达AI不同状态的emoji表情
   - 下方有用户输入窗口
   - AI回复以字幕形式显示在emoji下方(不是聊天气泡形式)
   - 同时播放AI回复的语音

2. **功能流程**：
   - 用户在输入框发送消息
   - AI状态emoji根据处理状态变化
   - 使用yunwu_helper.py调用AI生成文本回复
   - 使用test_tts.py将文本转换为语音
   - 显示文字字幕并播放语音

3. **技术栈**：
   - 后端：Python
   - 前端：Vue

## 项目规划

### 1. 架构设计

#### 前端部分 (Vue)
- **组件结构**：
  - AIEmoji组件：展示AI不同状态的emoji表情
  - UserInput组件：用户输入区域
  - SubtitleDisplay组件：显示AI回复字幕
  - AudioPlayer组件：处理语音播放

#### 后端部分 (Python)
- **Flask API**：
  - `/chat` 端点：接收用户消息，返回AI回复和语音文件URL
  - `/status` 端点：提供AI状态更新

### 2. AI状态设计
- **思考中**：显示思考emoji (例如：🤔)
- **回复中**：显示讲话emoji (例如：🗣️)
- **空闲状态**：默认表情 (例如：😊)
- **错误状态**：出错表情 (例如：😅)

### 3. 数据流设计
1. 用户发送消息 → 前端
2. 前端发送API请求 → 后端
3. 后端调用yunwu_helper.py获取AI回复
4. 后端使用test_tts.py将回复转为语音
5. 后端将文本和语音URL返回前端
6. 前端更新emoji状态、显示字幕并播放语音

### 4. 开发计划

#### 第一阶段：后端开发
1. 创建Flask应用，设置路由和端点
2. 集成yunwu_helper.py实现AI对话功能
3. 集成test_tts.py实现语音生成功能
4. 实现状态管理机制
5. 编写API文档

#### 第二阶段：前端开发
1. 初始化Vue项目
2. 设计UI界面布局
3. 实现各个组件功能
4. 集成API调用逻辑
5. 实现音频播放和emoji状态变化

#### 第三阶段：集成和测试
1. 前后端集成测试
2. 用户体验优化
3. 响应式设计调整
4. 性能优化

### 5. 技术要点

#### 后端实现关键点
- 使用Flask作为Web框架
- 使用WebSocket或轮询机制实现状态更新
- 将现有的yunwu_helper.py和test_tts.py转换为API服务

#### 前端实现关键点
- 使用Vue.js构建响应式UI
- 使用Axios处理API请求
- 使用Web Audio API处理音频播放
- 实现平滑的emoji状态过渡动画

请问您对这个规划有什么意见或建议？或者有什么细节需要我进一步解释的地方吗？
