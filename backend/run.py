import os
import sys
import subprocess
import argparse
import multiprocessing

def run_app(app_file, port):
    """运行指定的Flask应用"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, app_file)
    
    os.environ['FLASK_APP'] = app_path
    os.environ['FLASK_ENV'] = 'development'
    
    subprocess.run([sys.executable, app_path])

def main():
    parser = argparse.ArgumentParser(description='启动AI对话网站后端服务')
    parser.add_argument('--mode', type=str, choices=['normal', 'stream', 'both'], default='both',
                        help='运行模式：normal=普通模式，stream=流式模式，both=两种模式同时运行')
    
    args = parser.parse_args()
    
    if args.mode == 'normal':
        print("启动普通模式后端服务 (端口 8000)...")
        run_app('app.py', 8000)
    
    elif args.mode == 'stream':
        print("启动流式模式后端服务 (端口 8001)...")
        run_app('stream_app.py', 8001)
    
    elif args.mode == 'both':
        print("启动两种模式的后端服务...")
        
        # 创建进程分别运行两个应用
        p1 = multiprocessing.Process(target=run_app, args=('app.py', 8000))
        p2 = multiprocessing.Process(target=run_app, args=('stream_app.py', 8001))
        
        p1.start()
        p2.start()
        
        try:
            p1.join()
            p2.join()
        except KeyboardInterrupt:
            print("\n正在关闭服务...")
            p1.terminate()
            p2.terminate()
            p1.join()
            p2.join()
            print("服务已关闭！")

if __name__ == '__main__':
    main() 