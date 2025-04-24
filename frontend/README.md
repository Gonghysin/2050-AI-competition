# AI答题系统前端

本项目是AI答题系统的前端部分，基于Vue 3开发，提供和邪恶青蛙博士聊天和答题的交互界面。

## 功能特点

- 多情绪Emoji动画展示，反映AI不同状态
- 聊天界面支持多轮对话
- 支持三种题型的答题模式：选择题、判断题、简答题
- 完整的题目流程和得分反馈
- 响应式设计，适配移动端和桌面端

## 技术栈

- Vue 3 (组件化开发)
- Vuex (状态管理)
- Vue Router (路由管理)
- Axios (HTTP请求)
- SCSS (样式预处理)

## 项目结构

```
frontend/
├── public/                   # 静态资源
├── src/
│   ├── api/                  # API接口调用
│   ├── components/           # 公共组件
│   ├── pages/                # 页面组件
│   ├── store/                # Vuex存储
│   ├── router/               # 路由配置 
│   ├── styles/               # 全局样式
│   ├── App.vue               # 应用根组件
│   └── main.js               # 应用入口
```

## 快速开始

### 前提条件

- Node.js >= 14.x
- npm >= 6.x

### 安装依赖

```bash
cd frontend
npm install
```

### 开发运行

```bash
npm run serve
```

启动后访问: http://localhost:8080

### 构建生产版本

```bash
npm run build
```

生成的文件将位于 `dist/` 目录下

## 与后端通信

前端通过API与后端通信，主要接口：

- 创建会话: POST `/api/chat/create_session`
- 发送消息: POST `/api/chat/send`
- 获取历史: GET `/api/chat/history/{user_id}`
- 开始答题: POST `/api/quiz/start` 
- 提交答案: POST `/api/quiz/answer`

详细API文档请参考项目根目录下的 API文档.md

## 自定义配置

如需自定义配置，请参考 [Vue CLI配置参考](https://cli.vuejs.org/config/)。 