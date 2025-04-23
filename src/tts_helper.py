import os
import requests
import json
from typing import Optional, Union
import base64
from dotenv import load_dotenv
import io
import uuid

# 加载环境变量
load_dotenv()

class TTSHelper:
    """
    方舟豆包 TTS (Text-to-Speech) 助手类
    用于将文本转换为语音
    """
    
    def __init__(
        self, 
        app_id: str = "5171308068",
        access_token: str = "DMwm_fkqA4lHn9-WhsxnRpbERJRRLSkH",
        voice_type: str = "BV119_streaming",
        base_url: str = "https://openspeech.bytedance.com/api/v1/tts"
    ):
        """
        初始化 TTS 助手
        
        参数:
            app_id: 应用ID, 默认为README文档中提供的值
            access_token: 访问令牌, 默认为README文档中提供的值
            voice_type: 语音类型, 默认为README文档中提供的值
            base_url: API基础URL
        """
        self.app_id = app_id
        self.access_token = access_token
        self.voice_type = voice_type
        self.base_url = base_url
        
    def text_to_speech(
        self, 
        text: str, 
        output_file: Optional[str] = None,
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
        audio_format: str = "mp3"
    ) -> Union[bytes, str]:
        """
        将文本转换为语音
        
        参数:
            text: 需要转换为语音的文本
            output_file: 输出语音文件的路径，默认为None（返回音频数据）
            speed: 语速，默认为1.0，范围[0.2,3]
            volume: 音量，默认为1.0，范围[0.1,3]
            pitch: 音调，默认为1.0，范围[0.1,3]
            audio_format: 输出音频格式，默认为mp3，可选wav/pcm/ogg_opus/mp3
            
        返回:
            如果指定了output_file，则返回文件路径
            否则返回音频数据字节
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{self.access_token}"
        }
        
        # 准备请求体数据（根据官方文档规范）
        data = {
            "app": {
                "appid": self.app_id,
                "token": "access_token",
                "cluster": "volcano_tts"
            },
            "user": {
                "uid": "user_id"
            },
            "audio": {
                "voice_type": self.voice_type,
                "encoding": audio_format,
                "rate": 24000,
                "speed_ratio": speed,
                "volume_ratio": volume,
                "pitch_ratio": pitch
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query"
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data
            )
            
            # 检查响应状态
            if response.status_code != 200:
                raise Exception(f"API请求失败: {response.status_code}, {response.text}")
            
            # 解析响应数据
            result = response.json()
            
            # 检查响应中是否有错误
            if result.get("code") != 3000:  # 3000表示成功
                raise Exception(f"TTS转换失败: {result.get('message')}")
            
            # 获取音频数据（Base64编码）
            audio_data_base64 = result.get("data")
            
            if not audio_data_base64:
                raise Exception("响应中没有音频数据")
            
            # 解码Base64数据
            audio_bytes = base64.b64decode(audio_data_base64)
            
            # 如果指定了输出文件，则保存到文件
            if output_file:
                with open(output_file, "wb") as f:
                    f.write(audio_bytes)
                return output_file
            
            # 否则返回音频数据
            return audio_bytes
            
        except Exception as e:
            raise Exception(f"TTS转换过程中出错: {str(e)}")
    
    def text_to_speech_stream(
        self, 
        text: str, 
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
        audio_format: str = "mp3"
    ) -> io.BytesIO:
        """
        将文本转换为语音并返回一个流对象
        
        参数:
            text: 需要转换为语音的文本
            speed: 语速，默认为1.0
            volume: 音量，默认为1.0
            pitch: 音调，默认为1.0
            audio_format: 输出音频格式，默认为mp3
            
        返回:
            包含音频数据的BytesIO对象
        """
        audio_bytes = self.text_to_speech(
            text=text,
            speed=speed,
            volume=volume,
            pitch=pitch,
            audio_format=audio_format
        )
        
        return io.BytesIO(audio_bytes)


# 使用示例
if __name__ == "__main__":
    # 初始化TTS助手
    tts = TTSHelper()
    
    # 测试文本到语音转换
    text = "你好，这是一个测试。方舟豆包TTS服务非常好用！"
    
    # 方法1：保存到文件
    output_file = "tts_output.mp3"
    result = tts.text_to_speech(text, output_file)
    print(f"语音已保存到文件: {result}")
    
    # 方法2：获取音频数据
    audio_data = tts.text_to_speech(text)
    print(f"获取到音频数据，大小: {len(audio_data)} 字节")
    
    # 方法3：获取音频流
    audio_stream = tts.text_to_speech_stream(text)
    print(f"获取到音频流，大小: {audio_stream.getbuffer().nbytes} 字节")
