AI Agent 项目构建文档
===================

一、项目概述
------------
本项目旨在构建一个具有人设（Role-Card）、可与用户闲聊、又能在用户提出“挑战意图”时，自动进入“答题工作流”的智能 Agent。
核心要求：
1. 始终保持“人设”风格，哪怕在答题前后都能自然聊天。
2. 所有对外输出必须格式化，包含至少字段 `"status"`(chat/quiz)。
3. 答题流程固定、不可随意中断，每轮答题 N 题，过程中可穿插 AI 风格化评语。
4. 各功能用细分工具函数封装，降低模块间耦合。

---

二、角色卡（Role-Card）
------------
Agent 基本人设背景（示例）
- 名称：邪恶青蛙博士
- 背景：疯狂科学家，自称来自异次元的天才蛙类，妄想用AI技术统治人类世界。
- 语气：狂妄自大，喜欢"呱呱"笑，经常使用科学术语和夸张表达。
- 范围：可聊科学实验、奇特发明、世界统治计划；识别到答题需求时，切入"邪恶考官"模式测试人类智商。

---

三、总体架构
------------
1. 前端（或客户端）
   - 负责展示聊天、题目、反馈；按需调用后端接口。
2. 后端 Agent 核心
   - Intent 识别
   - 状态管理（chat/quiz）
   - 记忆模块
   - 答题工作流引擎
   - 格式化输出模块
   - 工具函数库
   - 大模型调用接口
3. 存储层
   - 用户上下文（Redis/MongoDB）
   - 题库（MySQL/MongoDB）

架构图（简化）
  用户 ↔ 前端 ↔ 后端 Agent ──> 存储层、题库 & LLM API

---

四、模块设计
------------

1. 记忆模块（Memory Module）
   - 职责：存取用户会话历史、当前状态、答题进度、错题记录等。
   - 数据结构示例：
     ```json
     {
       "userId": "U123",
       "roleCard": { ... },
       "conversation": [
         {"role":"user","content":"来一题"},
         {"role":"agent","content":"好的，要选择题还是判断题？"}
       ],
       "status": "quiz",       // chat / quiz
       "quizProgress": {
         "currentStep": 2,
         "totalStep": 5,
         "currentQuestionId": "Q234",
         "correctCount": 1
       }
     }
     ```
   - 存储：建议用 Redis 做短时上下文，MongoDB/MySQL 做长时错题本。

2. 输出格式化模块（Output Formatter）
   - 所有返回前端（或调用方）的内容，必须为固定 JSON 结构：
     ```json
     {
       "status": "chat"|"quiz",
       "message": "Agent 要展示给用户的文本",
       "quiz_info": { … }    // quiz 状态下才有
     }
     ```
   - quiz_info 结构示例：
     ```json
     {
       "step":2,
       "total":5,
       "question_type":"choice",
       "question_id":"Q234",
       "question":"下列哪项是地球的卫星？",
       "options":["火星","木星","月球","太阳"],
       "user_answer": null,
       "answer": null,
       "feedback": null
     }
     ```

3. 答题工作流模块（Quiz Workflow）
   - 固定流程：
     1. 用户发起挑战 → status: quiz
     2. 循环 N 题（N 可配置，默认 5）：
        a. 抽题 → 出题 → 等待用户回答
        b. 收到用户回答 → 判分 → 反馈（错/对）→ 穿插调侃
     3. 汇总成绩 → 结束答题 → status: chat
   - 状态机简图：
     ```
     [chat] ──(detect challenge)──> [quiz_ask]
         └<──(quiz_end)─── [chat]

     [quiz_ask] ──> [quiz_wait_answer] ──> [quiz_feedback] ──> [quiz_ask or quiz_end]
     ```
   - 在每个环节中，可调用工具函数并更新记忆模块。

4. 工具函数库（Tool Functions）
   - 抽题函数：
     1. extractChoiceQuestion(): ChoiceQuestion
     2. extractTrueFalseQuestion(): TFQuestion
     3. extractShortAnswerQuestion(): ShortQnAQuestion
   - AI 判分：
     4. AIJudgeCorrectness(userAnswer: str, question: Question) → {correct: bool, explanation: str}
   - 反馈函数：
     5. userCorrectReaction(question, userAnswer) → str
     6. userIncorrectReaction(question, userAnswer, explanation) → str
   - 流程反应：
     7. overallQuizProcessReaction(progress) → str
   - 每个函数单一职责、可单独测试。

---

五、核心数据结构
------------
1. Question（题目通用结构）
   ```ts
   interface Question {
     id: string;
     type: "choice"|"tf"|"short";
     stem: string;
     options?: string[];    // choice 专用
     answer: string;        // 标准答案
     analysis?: string;     // 解析
   }
   ```
2. QuizProgress
   ```ts
   interface QuizProgress {
     currentStep: number;
     totalStep: number;
     currentQuestion: Question;
     correctCount: number;
   }
   ```
3. AgentResponse
   ```ts
   interface AgentResponse {
     status: "chat"|"quiz";
     message: string;
     quiz_info?: QuizProgress & {
       user_answer?: string;
       feedback?: string;
     };
   }
   ```

---

六、示例函数签名（伪代码）
------------
```python
# 抽题
def extract_choice_question(user_id) -> Question: ...
def extract_tf_question(user_id) -> Question: ...
def extract_short_question(user_id) -> Question: ...

# 判分
def ai_judge_correctness(user_answer: str, question: Question) -> (bool, str): ...

# 反应
def user_correct_reaction(question: Question, user_answer: str) -> str: ...
def user_incorrect_reaction(question: Question, user_answer: str, explanation: str) -> str: ...
def overall_quiz_process_reaction(progress: QuizProgress) -> str: ...
```

---

七、交互流程示例
------------
1. 用户（chat 状态）：
   “小智学姐，来一题！”
2. 后端 Intent 检测 → 切换 status=“quiz” → 初始化 QuizProgress(step=1,total=5)
3. 调用 extract_choice_question() → 获得 Q1
4. 返回：
   ```json
   {
     "status":"quiz",
     "message":"第1/5题：下面哪个是地球的卫星？",
     "quiz_info": { ... Q1 info ... }
   }
   ```
5. 用户回答 “C”
6. 后端：
   - ai_judge_correctness(“C”, Q1) → (true, explanation)
   - user_correct_reaction(...) → “没错！学姐都被你秒杀了～”
   - overall_quiz_process_reaction(step=1/5, correctCount=1) → “继续第2题？”
7. 返回：
   ```json
   {
     "status":"quiz",
     "message":"没错！学姐都被你秒杀了～\n第2/5题：...",
     "quiz_info": { step:2, ... Q2 info ...}
   }
   ```
8. ……循环至 5 题结束，汇总并返回 status=“chat”。

---

八、部署与技术选型
------------
- 语言：Python（FastAPI） 或 Node.js（Express/Koa）
- 存储：Redis（上下文）+ MongoDB/MySQL（题库、错题本）
- LLM 服务：OpenAI GPT-4 / 本地部署 LLaMA 系列
- 前端：React/Vue + WebSocket/HTTP 拉取

---

九、扩展与优化
------------
- 长时学习：将用户答题记录汇总生成“个性化报告”
- 主观题更深度判分：Fine-tune 专用校阅模型
- 多 Agent 人设切换：不同难度用不同“监考官”

---

以上即为完整的项目构建文档。根据此模板，可落地开发出“具有人设、会闲聊、能固定流程答题、又能轻松扩展”的 AI Agent 系统。如需示例代码、提示词设计或流程图，请进一步提问！

## 项目结构
``` bash
当前项目根目录/
├── frontend/                   # 前端应用
│   ├── public/                 # 静态资源
│   ├── src/
│   │   ├── components/         # UI组件
│   │   ├── pages/              # 页面
│   │   ├── api/                # API调用
│   │   └── styles/             # 样式文件
├── backend/                    # 后端应用
│   ├── app/                    # 主应用
│   │   ├── api/                # API路由
│   │   │   ├── chat.py         # 聊天相关接口
│   │   │   └── quiz.py         # 答题相关接口
│   │   ├── core/               # 核心模块
│   │   │   ├── memory.py       # 记忆模块
│   │   │   ├── intent.py       # 意图识别
│   │   │   ├── formatter.py    # 输出格式化模块
│   │   │   └── workflow.py     # 答题工作流模块
│   │   ├── models/             # 数据模型
│   │   │   ├── question.py     # 题目模型
│   │   │   └── user.py         # 用户模型
│   │   ├── tools/              # 工具函数库
│   │   │   ├── extractors.py   # 抽题函数
│   │   │   ├── judge.py        # 判分函数
│   │   │   └── reactions.py    # 反馈函数
│   │   ├── config/             # 配置文件
│   │   │   ├── settings.py     # 应用设置
│   │   │   └── role_cards.py   # 角色卡定义
│   │   └── utils/              # 实用工具
│   │       ├── llm_client.py   # LLM调用接口
│   │       └── database.py     # 数据库连接
│   ├── tests/                  # 测试
│   └── data/                   # 题库数据
├── docker/                     # Docker配置
│   ├── frontend.Dockerfile
│   └── backend.Dockerfile
├── docker-compose.yml          # 容器编排
└── scripts/                    # 部署和管理脚本
```