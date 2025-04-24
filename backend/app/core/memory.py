import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import redis

from backend.app.models.user import UserSession, Message, RoleCard
from backend.app.utils.database import db_client

class MemoryManager:
    """记忆管理模块，负责存取用户会话历史、当前状态、答题进度等"""
    
    def __init__(self, redis_client=None):
        """初始化记忆管理器"""
        self.redis = redis_client or db_client.redis
        self.users = db_client.mongo.users
    
    def get_session(self, user_id: str) -> Optional[UserSession]:
        """
        获取用户会话
        先从Redis获取，若不存在则从MongoDB获取
        若MongoDB也不存在，返回None
        """
        # 先从Redis获取会话
        session_data = self.redis.get(f"session:{user_id}")
        if session_data:
            try:
                data = json.loads(session_data)
                return UserSession(**data)
            except Exception as e:
                print(f"Redis会话解析错误: {e}")
        
        # Redis没有，从MongoDB获取
        user_data = self.users.find_one({"user_id": user_id})
        if user_data:
            try:
                # 删除MongoDB自动添加的_id字段
                if "_id" in user_data:
                    del user_data["_id"]
                    
                session = UserSession(**user_data)
                # 将会话存入Redis
                self.save_session_to_redis(session)
                return session
            except Exception as e:
                print(f"MongoDB会话解析错误: {e}")
        
        return None
    
    def create_session(self, user_id: str, role_card: RoleCard) -> UserSession:
        """创建新的用户会话"""
        session = UserSession(
            user_id=user_id,
            role_card=role_card,
            conversation=[],
            status="chat",
            quiz_progress=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存到Redis和MongoDB
        self.save_session(session)
        return session
    
    def save_session(self, session: UserSession) -> None:
        """保存会话到Redis和MongoDB"""
        # 更新会话时间
        session.updated_at = datetime.now()
        
        # 保存到Redis
        self.save_session_to_redis(session)
        
        # 保存到MongoDB
        session_dict = session.dict()
        self.users.update_one(
            {"user_id": session.user_id},
            {"$set": session_dict},
            upsert=True
        )
    
    def save_session_to_redis(self, session: UserSession) -> None:
        """仅保存会话到Redis，有效期1小时"""
        session_json = session.json()
        self.redis.setex(
            f"session:{session.user_id}",
            3600,  # 1小时过期
            session_json
        )
    
    def add_message(self, user_id: str, role: str, content: str, audio_url: str = None) -> UserSession:
        """
        添加消息到会话
        
        参数:
            user_id: 用户ID
            role: 消息角色 "user" 或 "agent"
            content: 消息内容
            audio_url: 语音URL，仅对agent角色有效
            
        返回:
            更新后的会话对象
        """
        # 获取会话
        session = self.get_session(user_id)
        if not session:
            raise ValueError(f"未找到用户会话: {user_id}")
        
        # 添加消息
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            audio_url=audio_url if role == "agent" else None
        )
        session.conversation.append(message)
        
        # 保存会话
        self.save_session(session)
        return session
    
    def update_session_status(self, user_id: str, status: str) -> UserSession:
        """
        更新会话状态
        
        参数:
            user_id: 用户ID
            status: 新状态 "chat" 或 "quiz"
            
        返回:
            更新后的会话对象
        """
        # 获取会话
        session = self.get_session(user_id)
        if not session:
            raise ValueError(f"未找到用户会话: {user_id}")
        
        # 更新状态
        session.status = status
        
        # 保存会话
        self.save_session(session)
        return session
    
    def update_quiz_progress(self, user_id: str, quiz_progress: Dict[str, Any]) -> UserSession:
        """
        更新答题进度
        
        参数:
            user_id: 用户ID
            quiz_progress: 答题进度数据
            
        返回:
            更新后的会话对象
        """
        # 获取会话
        session = self.get_session(user_id)
        if not session:
            raise ValueError(f"未找到用户会话: {user_id}")
        
        # 更新答题进度
        session.quiz_progress = quiz_progress
        
        # 保存会话
        self.save_session(session)
        return session
    
    def get_conversation_history(self, user_id: str, max_messages: int = 10) -> List[Dict[str, str]]:
        """
        获取用户对话历史
        
        参数:
            user_id: 用户ID
            max_messages: 返回的最大消息数
            
        返回:
            格式化的对话历史，适合LLM输入
        """
        # 获取会话
        session = self.get_session(user_id)
        if not session:
            return []
        
        # 取最近的max_messages条消息
        recent_messages = session.conversation[-max_messages:] if len(session.conversation) > max_messages else session.conversation
        
        # 转换为LLM输入格式
        formatted_messages = []
        for msg in recent_messages:
            message_dict = {
                "role": "user" if msg.role == "user" else "agent",
                "content": msg.content
            }
            
            # 为agent消息添加audio_url
            if msg.role == "agent" and msg.audio_url:
                message_dict["audio_url"] = msg.audio_url
                
            formatted_messages.append(message_dict)
        
        return formatted_messages
        
    def clear_conversation_history(self, user_id: str) -> Optional[UserSession]:
        """
        清除用户的对话历史，但保留会话状态
        
        参数:
            user_id: 用户ID
            
        返回:
            更新后的会话对象，如果会话不存在则返回None
        """
        # 获取会话
        session = self.get_session(user_id)
        if not session:
            return None
        
        # 清空对话历史
        session.conversation = []
        
        # 保存会话
        self.save_session(session)
        return session

# 创建记忆管理器单例
memory_manager = MemoryManager() 