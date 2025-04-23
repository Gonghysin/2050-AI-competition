import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tts_helper import TTSHelper

def main():
    # 初始化TTS助手
    tts = TTSHelper()
    
    # 测试文本
    text = "你好，这是一个TTS测试。方舟豆包TTS服务非常好用！"
    
    # 保存到文件
    output_file = "tts_test_output.mp3"
    result = tts.text_to_speech(text, output_file)
    print(f"语音已保存到文件: {result}")
    
    # 测试不同参数
    # 高速版本
    fast_output = "tts_fast.mp3"
    tts.text_to_speech(text, fast_output, speed=1.5)
    print(f"快速语音已保存到文件: {fast_output}")
    
    # 低音版本
    low_pitch_output = "tts_low_pitch.mp3"
    tts.text_to_speech(text, low_pitch_output, pitch=0.8)
    print(f"低音语音已保存到文件: {low_pitch_output}")
    
    # 高音量版本
    loud_output = "tts_loud.mp3"
    tts.text_to_speech(text, loud_output, volume=1.5)
    print(f"高音量语音已保存到文件: {loud_output}")
    
    print("所有测试完成!")

if __name__ == "__main__":
    main() 