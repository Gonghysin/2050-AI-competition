from pymongo import MongoClient
from pymongo.database import Database
import redis
from redis import Redis
from typing import Optional
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    """数据库配置"""
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "ai_quiz_agent"
    REDIS_URI: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 允许额外的字段

class DatabaseClient:
    """数据库客户端"""
    _instance: Optional["DatabaseClient"] = None
    _mongo_client: Optional[MongoClient] = None
    _redis_client: Optional[Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
            cls._instance._init_clients()
        return cls._instance
    
    def _init_clients(self):
        """初始化数据库连接"""
        settings = DatabaseSettings()
        # MongoDB连接
        self._mongo_client = MongoClient(settings.MONGO_URI)
        # Redis连接
        self._redis_client = redis.from_url(settings.REDIS_URI)
    
    @property
    def mongo(self) -> Database:
        """获取MongoDB数据库实例"""
        settings = DatabaseSettings()
        return self._mongo_client[settings.MONGO_DB_NAME]
    
    @property
    def redis(self) -> Redis:
        """获取Redis客户端实例"""
        return self._redis_client
        
    def close(self):
        """关闭数据库连接"""
        if self._mongo_client:
            self._mongo_client.close()
        if self._redis_client:
            self._redis_client.close()

# 创建单例数据库客户端
db_client = DatabaseClient()

# MongoDB集合快捷访问
questions = db_client.mongo.questions
users = db_client.mongo.users
error_records = db_client.mongo.error_records