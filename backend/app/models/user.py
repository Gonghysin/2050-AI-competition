from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from uuid import UUID, uuid4

class RoleCard(BaseModel):
    """角色卡模型"""
    name: str  # 角色名称
    background: str  # 角色背景
    tone: str  # 语气特点
    scope: str  # 擅长范围
    
class Message(BaseModel):
    """消息模型"""
    role: Literal["user", "agent"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    audio_url: Optional[str] = None  # 消息的语音URL，仅对agent消息有效
    
class UserSession(BaseModel):
    """用户会话模型"""
    user_id: str
    role_card: RoleCard
    conversation: List[Message] = []
    status: Literal["chat", "quiz"] = "chat"
    quiz_progress: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
class UserErrorRecord(BaseModel):
    """用户错题记录"""
    user_id: str
    question_id: str
    question_type: Literal["choice", "tf", "short"]
    wrong_answers: List[str] = []  # 历史错误回答
    wrong_count: int = 0  # 错误次数
    last_wrong_at: datetime = Field(default_factory=datetime.now)