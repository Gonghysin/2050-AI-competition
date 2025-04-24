# AI答题系统 API 文档

本文档描述了AI答题系统的API接口，包括会话管理、聊天功能和答题流程等。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API前缀**: `/api`
- **内容类型**: 所有请求和响应均使用 `application/json`

## 健康检查

### 健康状态检查

检查API服务是否正常运行。

- **URL**: `/health`
- **方法**: `GET`
- **响应示例**:

```json
{
  "status": "ok"
}
```

## 聊天API

### 创建会话

创建新的聊天会话，并返回用户ID和初始问候语。

- **URL**: `/api/chat/create_session`
- **方法**: `POST`
- **请求参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| role_card_id | string | 是 | 角色卡ID，如"evil_frog"或"smart_sister" |

- **请求示例**:

```json
{
  "role_card_id": "evil_frog"
}
```

- **响应示例**:

```json
{
  "user_id": "user_abcd1234",
  "role_card": {
    "name": "邪恶青蛙博士",
    "background": "一个邪恶的科学家，喜欢出各种刁钻的问题...",
    "avatar": "frog.png",
    "description": "喜欢考验人类智慧的邪恶青蛙博士"
  },
  "greeting": "呱呱呱，人类！准备好接受我的智力挑战了吗？"
}
```

### 发送消息

向AI发送消息，并获取回复。

- **URL**: `/api/chat/send`
- **方法**: `POST`
- **请求参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |
| message | string | 是 | 用户消息内容 |
| role_card_id | string | 否 | 角色卡ID，可选，用于切换角色 |

- **请求示例**:

```json
{
  "user_id": "user_abcd1234",
  "message": "你好，我想挑战一下你的题目"
}
```

- **响应示例**:

```json
{
  "status": "chat",
  "message": "呱呱呱！很好，人类！你准备好接受我的挑战了吗？我有一些精心准备的问题等着你！确认要开始答题吗？",
  "quiz_info": null
}
```

### 获取聊天历史

获取特定用户的聊天历史记录。

- **URL**: `/api/chat/history/{user_id}`
- **方法**: `GET`
- **URL参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

- **查询参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| limit | integer | 否 | 返回的历史消息数量限制，默认20 |

- **响应示例**:

```json
[
  {
    "role": "agent",
    "content": "呱呱呱，人类！准备好接受我的智力挑战了吗？",
    "timestamp": "2023-04-24T10:30:00Z"
  },
  {
    "role": "user",
    "content": "你好，我想挑战一下你的题目",
    "timestamp": "2023-04-24T10:31:00Z"
  },
  {
    "role": "agent",
    "content": "呱呱呱！很好，人类！你准备好接受我的挑战了吗？我有一些精心准备的问题等着你！确认要开始答题吗？",
    "timestamp": "2023-04-24T10:31:05Z"
  }
]
```

### 删除会话

删除特定用户的聊天会话。

- **URL**: `/api/chat/session/{user_id}`
- **方法**: `DELETE`
- **URL参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

- **响应示例**:

```json
{
  "status": "success",
  "message": "会话已删除"
}
```

### 获取角色卡列表

获取所有可用的角色卡信息。

- **URL**: `/api/chat/role_cards`
- **方法**: `GET`
- **响应示例**:

```json
{
  "evil_frog": {
    "name": "邪恶青蛙博士",
    "avatar": "frog.png",
    "description": "喜欢考验人类智慧的邪恶青蛙博士"
  },
  "smart_sister": {
    "name": "聪明学姐",
    "avatar": "sister.png",
    "description": "知识渊博、温柔可亲的学姐"
  }
}
```

## 答题API

### 开始答题

开始答题流程，返回第一题。

- **URL**: `/api/quiz/start`
- **方法**: `POST`
- **请求参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |
| total_questions | integer | 否 | 题目总数，默认3 |
| question_types | array | 否 | 题目类型列表，如["tf", "choice", "short"] |

- **请求示例**:

```json
{
  "user_id": "user_abcd1234",
  "total_questions": 3
}
```

- **响应示例**:

```json
{
  "status": "quiz",
  "message": "第1/3题：下列哪个选项是JavaScript的正确特性？",
  "quiz_info": {
    "step": 1,
    "total": 3,
    "question_type": "choice",
    "question_id": "q_123456",
    "question": "下列哪个选项是JavaScript的正确特性？",
    "options": [
      "JavaScript是一种强类型语言",
      "JavaScript只能在浏览器中运行",
      "JavaScript是基于原型的面向对象语言",
      "JavaScript只支持同步编程"
    ],
    "user_answer": null,
    "answer": null,
    "feedback": null
  }
}
```

### 提交答案

提交用户的答案，并获取反馈和下一题。

- **URL**: `/api/quiz/answer`
- **方法**: `POST`
- **请求参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |
| answer | string | 是 | 用户答案 |

- **请求示例**:

```json
{
  "user_id": "user_abcd1234",
  "answer": "C"
}
```

- **响应示例**:

```json
{
  "status": "quiz",
  "message": "正确！JavaScript确实是基于原型的面向对象语言。下面是第2/3题：请问布尔值true和字符串'true'在JavaScript中是否相等？",
  "quiz_info": {
    "step": 1,
    "total": 3,
    "question_type": "choice",
    "question_id": "q_123456",
    "question": "下列哪个选项是JavaScript的正确特性？",
    "options": [
      "JavaScript是一种强类型语言",
      "JavaScript只能在浏览器中运行",
      "JavaScript是基于原型的面向对象语言",
      "JavaScript只支持同步编程"
    ],
    "user_answer": "C",
    "answer": "C",
    "feedback": "正确！JavaScript确实是基于原型的面向对象语言。"
  }
}
```

### 获取下一题

获取下一道题目，用于在用户答题后跳转到下一题。

- **URL**: `/api/quiz/next/{user_id}`
- **方法**: `GET`
- **URL参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

- **响应示例**:

```json
{
  "status": "quiz",
  "message": "第2/3题：请问布尔值true和字符串'true'在JavaScript中是否相等？",
  "quiz_info": {
    "step": 2,
    "total": 3,
    "question_type": "tf",
    "question_id": "q_234567",
    "question": "请问布尔值true和字符串'true'在JavaScript中是否相等？",
    "options": null,
    "user_answer": null,
    "answer": null,
    "feedback": null
  }
}
```

### 结束答题

手动结束答题流程，返回总结结果。

- **URL**: `/api/quiz/end/{user_id}`
- **方法**: `POST`
- **URL参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

- **响应示例**:

```json
{
  "status": "chat",
  "message": "呱呱呱！你已完成所有题目！最终得分：2/3，正确率：66.7%。表现不错，人类！",
  "quiz_info": {
    "step": 3,
    "total": 3,
    "correct_count": 2,
    "score": 66.7,
    "completed": true
  }
}
```

### 获取答题进度

获取用户当前的答题进度。

- **URL**: `/api/quiz/progress/{user_id}`
- **方法**: `GET`
- **URL参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

- **响应示例**:

```json
{
  "status": "in_progress",
  "progress": {
    "current_step": 2,
    "total_step": 3,
    "current_question_id": "q_234567",
    "correct_count": 1,
    "state": "quiz_wait_answer",
    "answered_questions": ["q_123456"]
  }
}
```

### 获取答题历史

获取用户的答题历史记录。

- **URL**: `/api/quiz/history/{user_id}`
- **方法**: `GET`
- **URL参数**:

| 参数 | 类型 | 必须 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

- **响应示例**:

```json
[
  {
    "quiz_id": "quiz_12345",
    "timestamp": "2023-04-24T11:30:00Z",
    "total_questions": 3,
    "correct_count": 2,
    "score": 66.7,
    "questions": [
      {
        "question_id": "q_123456",
        "question": "下列哪个选项是JavaScript的正确特性？",
        "user_answer": "C",
        "correct_answer": "C",
        "is_correct": true
      },
      {
        "question_id": "q_234567",
        "question": "请问布尔值true和字符串'true'在JavaScript中是否相等？",
        "user_answer": "是",
        "correct_answer": "否",
        "is_correct": false
      },
      {
        "question_id": "q_345678",
        "question": "简述JavaScript中闭包的概念及其作用。",
        "user_answer": "闭包是指有权访问另一个函数作用域中变量的函数...",
        "is_correct": true
      }
    ]
  }
]
```

## 错误响应

所有API可能返回以下错误响应：

### 404 Not Found

```json
{
  "detail": "会话不存在"
}
```

### 400 Bad Request

```json
{
  "detail": "当前不在答题模式"
}
```

### 500 Internal Server Error

```json
{
  "detail": "服务器内部错误"
}
```

## 常见状态码

- **200**: 请求成功
- **400**: 请求参数错误
- **404**: 资源不存在
- **500**: 服务器内部错误

## 数据模型

### AgentResponse

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | 当前状态，如"chat"或"quiz" |
| message | string | AI回复消息 |
| quiz_info | QuizInfo | 答题信息，仅在答题模式下返回 |

### QuizInfo

| 字段 | 类型 | 描述 |
|------|------|------|
| step | integer | 当前题目序号 |
| total | integer | 总题目数量 |
| question_type | string | 题目类型，如"choice"、"tf"或"short" |
| question_id | string | 题目ID |
| question | string | 题目内容 |
| options | array | 选择题选项，仅选择题返回 |
| user_answer | string | 用户答案 |
| answer | string | 正确答案 |
| feedback | string | 答题反馈 |

## 示例流程

1. 创建会话
2. 与AI聊天
3. 用户表达答题意愿
4. AI切换到答题模式
5. 开始答题流程
6. 用户回答题目并获取反馈
7. 完成所有题目后返回总结
8. 回到聊天模式 