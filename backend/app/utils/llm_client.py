import os
import requests
import json
from typing import Dict, List, Optional, Union, Generator
from pydantic_settings import BaseSettings
from backend.app.models.response import AgentResponse, QuizInfo

class LLMSettings(BaseSettings):
    """LLM配置"""
    YUNWU_DEFAULT_API_KEY: str = ""
    YUNWU_AZ_API_KEY: str = ""
    BOCHA_API_KEY: str = ""
    FIRECRAWL_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        extra = "ignore"

class LLMClient:
    """
    LLM客户端，支持多种模型
    默认使用OpenRouter API
    """
    
    def __init__(self, provider: str = "openrouter", api_key_group: str = "default", base_url: str = "https://openrouter.ai/api/v1"):
        """
        初始化LLM客户端
        
        参数:
            provider: LLM提供商，如openrouter, yunwu, bocha, firecrawl等
            api_key_group: API密钥分组，yunwu可选值为"default"或"az"
            base_url: API基础URL
        """
        self.settings = LLMSettings()
        self.provider = provider.lower()
        self.base_url = base_url
        
        # 根据提供商和分组选择对应的API密钥
        if self.provider == "openrouter":
            self.api_key = self.settings.OPENROUTER_API_KEY
            self.available_models = ["google/gemini-2.5-flash-preview", "openai/gpt-4o"]
            self.default_model = "google/gemini-2.5-flash-preview"
            
        elif self.provider == "yunwu":
            if api_key_group.lower() == "default":
                self.api_key = self.settings.YUNWU_DEFAULT_API_KEY
            elif api_key_group.lower() == "az":
                self.api_key = self.settings.YUNWU_AZ_API_KEY
            else:
                raise ValueError(f"不支持的API密钥分组: {api_key_group}，可用分组: default, az")
            
            self.available_models = ["gemini-2.5-flash-preview-04-17", "deepseek-r1", "gpt-4o"]
            self.default_model = "gemini-2.5-flash-preview-04-17"
        
        elif self.provider == "bocha":
            self.api_key = self.settings.BOCHA_API_KEY
            self.available_models = ["360GPT-S2"]
            self.default_model = "360GPT-S2"
        
        elif self.provider == "firecrawl":
            self.api_key = self.settings.FIRECRAWL_API_KEY
            self.available_models = ["Firecrawl-LLM"]
            self.default_model = "Firecrawl-LLM"
        
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")
        
        if not self.api_key:
            raise ValueError(f"未找到{provider}/{api_key_group}的API密钥，请检查.env文件")
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             model: str = None, 
             temperature: float = 0.7, 
             max_tokens: int = 1000) -> Dict:
        """
        与LLM进行对话
        
        参数:
            messages: 对话消息列表，格式为[{"role": "user", "content": "你好"}]
            model: 使用的模型，不同提供商有不同的模型
            temperature: 温度参数，控制输出的随机性
            max_tokens: 生成的最大token数
            
        返回:
            完整的API响应
        """
        # 如果未指定模型，使用提供商默认模型
        if model is None:
            model = self.default_model
        
        if model not in self.available_models:
            raise ValueError(f"不支持的模型: {model}，可用模型: {', '.join(self.available_models)}")
        
        # OpenRouter
        if self.provider == "openrouter":
            return self._openrouter_chat(messages, model, temperature, max_tokens)
        # 云雾AI
        elif self.provider == "yunwu":
            return self._yunwu_chat(messages, model, temperature, max_tokens)
        # 博查AI
        elif self.provider == "bocha":
            return self._bocha_chat(messages, model, temperature, max_tokens)
        # 火爬
        elif self.provider == "firecrawl":
            return self._firecrawl_chat(messages, model, temperature, max_tokens)
    
    def _openrouter_chat(self, messages, model, temperature, max_tokens):
        """OpenRouter API调用实现"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://2050-ai-competition.com",  # 可以根据实际情况修改
            "X-Title": "2050 AI Competition"  # 可以根据实际情况修改
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, {response.text}")
        
        return response.json()
    
    def _yunwu_chat(self, messages, model, temperature, max_tokens):
        """云雾API调用实现"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, {response.text}")
        
        return response.json()
    
    def _bocha_chat(self, messages, model, temperature, max_tokens):
        """博查API调用实现"""
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        data = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, {response.text}")
        
        return response.json()
    
    def _firecrawl_chat(self, messages, model, temperature, max_tokens):
        """火爬API调用实现"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
        
        data = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, {response.text}")
        
        return response.json()
    
    def chat_stream(self, 
                   messages: List[Dict[str, str]], 
                   model: str = None, 
                   temperature: float = 0.7, 
                   max_tokens: int = 1000) -> Generator[str, None, None]:
        """
        与LLM进行流式对话
        
        参数:
            messages: 对话消息列表，格式为[{"role": "user", "content": "你好"}]
            model: 使用的模型
            temperature: 温度参数，控制输出的随机性
            max_tokens: 生成的最大token数
            
        返回:
            生成器，每次返回一个文本片段
        """
        # 如果未指定模型，使用提供商默认模型
        if model is None:
            model = self.default_model
            
        if model not in self.available_models:
            raise ValueError(f"不支持的模型: {model}，可用模型: {', '.join(self.available_models)}")
        
        # OpenRouter流式API
        if self.provider == "openrouter":
            yield from self._openrouter_stream(messages, model, temperature, max_tokens)
        # 云雾流式API
        elif self.provider == "yunwu":
            yield from self._yunwu_stream(messages, model, temperature, max_tokens)
        else:
            response = self.chat(messages, model, temperature, max_tokens)
            content = response["choices"][0]["message"]["content"]
            yield content
    
    def _openrouter_stream(self, messages, model, temperature, max_tokens):
        """OpenRouter流式API调用实现"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://2050-ai-competition.com",
            "X-Title": "2050 AI Competition"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            stream=True
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, {response.text}")
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]  # 移除 "data: " 前缀
                    if line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        if chunk.get('choices') and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta and delta['content']:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue
    
    def _yunwu_stream(self, messages, model, temperature, max_tokens):
        """云雾流式API调用实现"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=data,
            stream=True
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, {response.text}")
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]  # 移除 "data: " 前缀
                    if line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        if chunk.get('choices') and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta and delta['content']:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue

    def chat_with_format(self, 
                        user_message: str, 
                        role_card: Dict, 
                        conversation_history: List[Dict[str, str]] = None,
                        status: str = "chat",
                        quiz_info: Dict = None,
                        model: str = None,
                        temperature: float = 0.7) -> AgentResponse:
        """
        与LLM对话并返回格式化的响应
        
        参数:
            user_message: 用户消息
            role_card: 角色卡信息
            conversation_history: 对话历史
            status: 当前状态，"chat"或"quiz"
            quiz_info: 答题相关信息
            model: 使用的模型
            temperature: 温度参数
            
        返回:
            格式化的Agent响应
        """
        # 构建系统提示
        system_message = self._build_system_prompt(role_card, status, quiz_info)
        
        # 构建完整的消息历史
        messages = [{"role": "system", "content": system_message}]
        
        # 添加对话历史
        if conversation_history:
            messages.extend(conversation_history)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 调用LLM
        response = self.chat(messages, model, temperature)
        response_content = response["choices"][0]["message"]["content"]
        
        # 解析格式化响应
        try:
            json_response = json.loads(response_content)
            
            # 将JSON字段映射到AgentResponse模型
            agent_response = AgentResponse(
                status=json_response.get("status", status),
                message=json_response.get("message", ""),
                quiz_info=QuizInfo(**json_response.get("quiz_info")) if json_response.get("quiz_info") else None
            )
            
            return agent_response
        except json.JSONDecodeError:
            # 如果无法解析JSON，返回原始文本作为消息
            return AgentResponse(
                status=status,
                message=response_content
            )
    
    def _build_system_prompt(self, role_card: Dict, status: str, quiz_info: Dict = None) -> str:
        """构建系统提示"""
        prompt = f"""你是一个AI助手，正在扮演以下角色：

名称：{role_card.get('name', '邪恶青蛙博士')}
背景：{role_card.get('background', '疯狂科学家，自称来自异次元的天才蛙类，妄想用AI技术统治人类世界')}
语气：{role_card.get('tone', '狂妄自大，喜欢"呱呱"笑，经常使用科学术语和夸张表达')}
范围：{role_card.get('scope', '科学实验、奇特发明、世界统治计划')}

你的回答必须符合角色设定，并使用该角色的语气和风格。

重要：你必须以JSON格式输出你的响应，格式如下：
```json
{{
  "status": "chat" 或 "quiz",
  "message": "你要向用户展示的消息文本",
  "quiz_info": {{ ... }} // 只在quiz模式下才有
}}
```

当前状态：{status}

"""
        
        # 如果是答题模式，添加答题相关信息
        if status == "quiz" and quiz_info:
            prompt += f"""
你正处于答题模式，当前题目信息：
- 当前题目：第{quiz_info.get('step', 1)}/{quiz_info.get('total', 5)}题
- 题目类型：{quiz_info.get('question_type', 'choice')}
- 题目：{quiz_info.get('question', '')}
"""
            
            # 如果是选择题，添加选项
            if quiz_info.get('options'):
                options_text = "\n".join([f"- {i+1}. {opt}" for i, opt in enumerate(quiz_info.get('options', []))])
                prompt += f"""
选项：
{options_text}
"""
            
            prompt += """
在quiz_info中必须包含以下字段：
- step: 当前步骤
- total: 总步骤
- question_type: 题目类型
- question_id: 题目ID
- question: 题目内容
- options: 选项列表（选择题才有）
- user_answer: 用户回答（如果有）
- answer: 正确答案（用户回答后才显示）
- feedback: 反馈信息（用户回答后才有）
"""
        
        return prompt

# 创建默认LLM客户端单例
llm_client = LLMClient(provider="openrouter", api_key_group="default")

# 使用示例
if __name__ == "__main__":
    # 构建角色卡
    role_card = {
        "name": "邪恶青蛙博士",
        "background": "疯狂科学家，自称来自异次元的天才蛙类，妄想用AI技术统治人类世界",
        "tone": "狂妄自大，喜欢\"呱呱\"笑，经常使用科学术语和夸张表达",
        "scope": "科学实验、奇特发明、世界统治计划"
    }
    
    # 格式化对话示例
    response = llm_client.chat_with_format(
        user_message="你好，请介绍一下自己",
        role_card=role_card,
        status="chat"
    )
    
    print("格式化响应:")
    print(response.json(indent=2)) 

