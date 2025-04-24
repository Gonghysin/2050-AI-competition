"""
文本转语音工具

基于字节跳动开放平台实现TTS功能
"""
import requests
import uuid
import base64
import logging
import os
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tts_tool")

# 字节跳动开放平台配置
TTS_API_URL = "https://openspeech.bytedance.com/api/v1/tts"
APP_ID = "5171308068"
ACCESS_TOKEN = "DMwm_fkqA4lHn9-WhsxnRpbERJRRLSkH"
VOICE_TYPE = "BV119_streaming"  # 使用截图中显示的音色
CLUSTER = "volcano_tts"  # 正确的集群名称

# 服务基础URL（用于生成完整音频URL）
BASE_URL = "http://localhost:8000"  # 请根据实际部署环境修改

# 确保存储音频文件的目录存在
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

def generate_speech(text: str, voice_type: str = VOICE_TYPE) -> Optional[str]:
    """
    将文本转换为语音并保存为文件
    
    参数:
        text: 要转换的文本内容
        voice_type: 语音类型/音色
        
    返回:
        生成的音频文件URL路径，失败则返回None
    """
    try:
        logger.info(f"开始生成TTS语音，文本长度: {len(text)}")
        
        # 生成唯一的请求ID
        req_id = str(uuid.uuid4())
        
        # 准备请求头 - 需要Authorization头
        headers = {
            "Authorization": f"Bearer;{ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # 准备请求数据
        payload = {
            "app": {
                "appid": APP_ID,
                "cluster": CLUSTER
            },
            "user": {
                "uid": APP_ID  # 使用APP_ID作为用户ID
            },
            "audio": {
                "voice_type": voice_type,
                "encoding": "wav",
                "rate": 24000,
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0
            },
            "request": {
                "reqid": req_id,
                "text": text,
                "text_type": "plain",
                "operation": "query"
            }
        }
        
        # 发送请求
        logger.info(f"发送TTS请求，请求ID: {req_id}")
        response = requests.post(TTS_API_URL, json=payload, headers=headers)
        
        # 检查请求是否成功
        if response.status_code != 200:
            logger.error(f"TTS请求失败: {response.status_code}, {response.text}")
            return None
        
        # 解析响应数据
        result = response.json()
        # 检查是否成功
        if result.get("code") != 3000:  # 正确的成功码是3000
            logger.error(f"TTS生成失败: {result.get('code')}, {result.get('message')}")
            return None
        
        # 获取Base64编码的音频数据
        audio_base64 = result.get("data", "")  # 音频数据直接在data字段
        if not audio_base64:
            logger.error("返回的音频数据为空")
            return None
            
        # 记录音频时长信息（如果有）
        if "addition" in result and "duration" in result["addition"]:
            logger.info(f"音频时长: {result['addition']['duration']}ms")
        
        # 解码Base64音频数据
        try:
            audio_data = base64.b64decode(audio_base64)
            logger.info(f"音频数据解码成功，大小: {len(audio_data)} 字节")
        except Exception as e:
            logger.error(f"音频数据解码失败: {e}")
            return None
        
        # 保存音频文件
        audio_filename = f"{req_id}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        with open(audio_path, "wb") as audio_file:
            audio_file.write(audio_data)
            
        logger.info(f"TTS语音生成成功，文件保存至: {audio_path}")
        
        # 返回音频文件的相对URL
        return f"/static/audio/{audio_filename}"
        
    except Exception as e:
        logger.error(f"TTS生成异常: {e}", exc_info=True)
        return None

def text_to_speech_url(text: str) -> Optional[str]:
    """
    将文本转换为语音并返回可访问的URL
    
    参数:
        text: 要转换的文本
        
    返回:
        语音文件的URL，失败则返回None
    """
    # 文本太长则截断
    if len(text) > 500:
        text = text[:497] + "..."
    
    # 过滤掉不必要的字符
    text = text.replace('【正确答案】', '正确答案是')
    
    # 生成语音
    audio_url = generate_speech(text)
    
    # 如果生成成功，添加基础URL前缀
    if audio_url:
        return f"{BASE_URL}{audio_url}"
    
    return audio_url 