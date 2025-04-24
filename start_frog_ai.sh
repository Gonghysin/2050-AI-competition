#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 打印带颜色的消息
echo -e "${GREEN}===== 邪恶青蛙AI启动脚本 =====${NC}"
echo -e "${BLUE}检查项目环境...${NC}"

# 检查当前目录
PROJECT_ROOT=$(dirname "$(realpath "$0")")
cd "$PROJECT_ROOT"

echo -e "${BLUE}当前工作目录: $(pwd)${NC}"

# 检查后端服务是否已经在运行
PORT_CHECK=$(lsof -i:8000 | grep LISTEN)
if [ -n "$PORT_CHECK" ]; then
    echo -e "${YELLOW}警告: 8000端口已被占用，可能是服务已经在运行${NC}"
    echo -e "${YELLOW}正在运行的进程:${NC}"
    echo "$PORT_CHECK"
    
    read -p "是否继续启动? (y/n): " CONTINUE
    if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
        echo -e "${RED}取消启动${NC}"
        exit 1
    fi
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3${NC}"
    exit 1
fi

# 检查是否有虚拟环境
if [ -d "venv" ]; then
    echo -e "${BLUE}检测到虚拟环境，激活中...${NC}"
    source venv/bin/activate || source venv/Scripts/activate
elif [ -d ".venv" ]; then
    echo -e "${BLUE}检测到虚拟环境，激活中...${NC}"
    source .venv/bin/activate || source .venv/Scripts/activate
elif [ -d "env" ]; then
    echo -e "${BLUE}检测到虚拟环境，激活中...${NC}"
    source env/bin/activate || source env/Scripts/activate
else
    echo -e "${YELLOW}警告: 未检测到虚拟环境，使用系统Python${NC}"
fi

# 检查依赖项
echo -e "${BLUE}检查依赖项...${NC}"
python -c "import flask, flask_cors" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}警告: 缺少必要依赖，尝试安装...${NC}"
    pip install flask flask-cors
fi

# 启动新版青蛙AI服务
echo -e "${GREEN}正在启动青蛙AI服务...${NC}"
cd backend
nohup python run_v2.py --mode v2 > ../frog_ai.log 2>&1 &

# 获取进程ID
PID=$!
echo $PID > ../frog_ai.pid

# 检查服务是否成功启动
sleep 2
if ps -p $PID > /dev/null; then
    echo -e "${GREEN}青蛙AI服务已成功启动! 进程ID: $PID${NC}"
    echo -e "${GREEN}日志文件: $(pwd)/../frog_ai.log${NC}"
    echo -e "${BLUE}服务地址: http://localhost:8000${NC}"
    echo -e "${YELLOW}提示: 使用 './stop_frog_ai.sh' 停止服务${NC}"
else
    echo -e "${RED}启动失败，请检查日志文件: $(pwd)/../frog_ai.log${NC}"
    exit 1
fi

# 启动前端开发服务器(如果需要)
read -p "是否启动前端开发服务器? (y/n): " START_FRONTEND
if [[ "$START_FRONTEND" == "y" || "$START_FRONTEND" == "Y" ]]; then
    echo -e "${BLUE}正在启动前端开发服务器...${NC}"
    cd ../frontend
    if [ -f "package.json" ]; then
        nohup npm run serve > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../frontend.pid
        echo -e "${GREEN}前端开发服务器已启动! 进程ID: $FRONTEND_PID${NC}"
        echo -e "${GREEN}日志文件: $(pwd)/../frontend.log${NC}"
        echo -e "${BLUE}访问地址: http://localhost:8080${NC}"
    else
        echo -e "${RED}未找到package.json文件，无法启动前端服务${NC}"
    fi
fi

echo -e "${GREEN}===== 启动完成 =====${NC}" 