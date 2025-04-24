#!/usr/bin/env python
import os
import sys
import argparse
import subprocess
import logging
import threading
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [run_v2] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('run_v2')

def run_server(app_module, port, stop_event):
    """运行指定的服务器应用"""
    logger.info(f"启动 {app_module} 服务器，端口: {port}")
    
    # 获取当前脚本所在目录路径
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(backend_dir, app_module)
    
    # 检查应用文件是否存在
    if not os.path.exists(app_path):
        logger.error(f"应用文件不存在: {app_path}")
        return
    
    # 启动进程
    try:
        process = subprocess.Popen(
            [sys.executable, app_path],
            env={**os.environ, "FLASK_APP": app_module, "FLASK_ENV": "development", "PORT": str(port)}
        )
        
        logger.info(f"{app_module} 服务器进程已启动，PID: {process.pid}")
        
        # 等待停止事件或进程结束
        while not stop_event.is_set() and process.poll() is None:
            time.sleep(0.5)
        
        # 如果进程仍在运行并且收到停止事件，终止进程
        if process.poll() is None:
            logger.info(f"正在终止 {app_module} 服务器进程...")
            process.terminate()
            process.wait(timeout=5)
        
        logger.info(f"{app_module} 服务器已停止，返回码: {process.returncode}")
    
    except Exception as e:
        logger.error(f"运行 {app_module} 出错: {str(e)}", exc_info=True)

def main():
    """主函数，处理命令行参数并启动服务器"""
    parser = argparse.ArgumentParser(description="启动青蛙AI应用服务器")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["v1", "v2", "both"], 
        default="v2",
        help="选择启动的应用版本: v1=旧版, v2=新版, both=同时启动两者"
    )
    
    args = parser.parse_args()
    
    # 停止事件，用于终止服务器线程
    stop_event = threading.Event()
    
    # 服务器线程列表
    threads = []
    
    try:
        if args.mode in ["v1", "both"]:
            # 启动旧版应用
            logger.info("准备启动旧版应用...")
            v1_thread = threading.Thread(
                target=run_server,
                args=("app.py", 8000, stop_event),
                name="v1_thread"
            )
            v1_thread.start()
            threads.append(v1_thread)
            
            # 启动流式应用
            logger.info("准备启动旧版流式应用...")
            stream_thread = threading.Thread(
                target=run_server,
                args=("stream_app.py", 8001, stop_event),
                name="stream_thread"
            )
            stream_thread.start()
            threads.append(stream_thread)
        
        if args.mode in ["v2", "both"]:
            # 启动新版应用
            port = 8002 if args.mode == "both" else 8000
            logger.info("准备启动新版应用...")
            v2_thread = threading.Thread(
                target=run_server,
                args=("app_v2.py", port, stop_event),
                name="v2_thread"
            )
            v2_thread.start()
            threads.append(v2_thread)
        
        # 等待所有线程结束
        for thread in threads:
            thread.join()
    
    except KeyboardInterrupt:
        logger.info("收到终止信号，正在关闭服务器...")
        stop_event.set()
        
        # 等待所有线程结束
        for thread in threads:
            thread.join(timeout=10)
        
        logger.info("服务器已关闭")
    
    except Exception as e:
        logger.error(f"运行出错: {str(e)}", exc_info=True)
        stop_event.set()
        
        # 等待所有线程结束
        for thread in threads:
            thread.join(timeout=10)

if __name__ == "__main__":
    main() 