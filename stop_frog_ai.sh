#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

echo -e "${RED}===== 邪恶青蛙AI关闭脚本 =====${NC}"

# 检查当前目录
PROJECT_ROOT=$(dirname "$(realpath "$0")")
cd "$PROJECT_ROOT"

echo -e "${BLUE}当前工作目录: $(pwd)${NC}"

# 尝试从PID文件关闭服务
if [ -f "frog_ai.pid" ]; then
    PID=$(cat frog_ai.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}正在关闭青蛙AI服务 (PID: $PID)...${NC}"
        kill $PID
        sleep 2
        
        # 验证进程是否已关闭
        if ! ps -p $PID > /dev/null; then
            echo -e "${GREEN}✓ 青蛙AI服务已成功关闭${NC}"
            rm frog_ai.pid
        else
            echo -e "${RED}无法正常关闭服务，尝试强制终止...${NC}"
            kill -9 $PID
            sleep 1
            echo -e "${YELLOW}已强制终止服务${NC}"
            rm frog_ai.pid
        fi
    else
        echo -e "${YELLOW}PID文件中的进程 ($PID) 不存在${NC}"
        rm frog_ai.pid
    fi
else
    echo -e "${YELLOW}未找到PID文件，尝试查找并关闭所有相关进程...${NC}"
fi

# 尝试通过端口关闭服务
PORT_PROCESSES=$(lsof -i:8000 | grep "python" | awk '{print $2}')
if [ -n "$PORT_PROCESSES" ]; then
    echo -e "${YELLOW}发现在8000端口运行的Python进程，正在关闭...${NC}"
    for pid in $PORT_PROCESSES; do
        echo -e "${BLUE}关闭进程 $pid...${NC}"
        kill $pid
    done
    
    # 验证进程是否已关闭
    sleep 2
    if [ -z "$(lsof -i:8000)" ]; then
        echo -e "${GREEN}✓ 所有8000端口的进程已关闭${NC}"
    else
        echo -e "${RED}某些进程无法正常关闭，尝试强制终止...${NC}"
        for pid in $PORT_PROCESSES; do
            kill -9 $pid 2>/dev/null
        done
        echo -e "${YELLOW}已强制终止所有进程${NC}"
    fi
else
    echo -e "${BLUE}未发现在8000端口运行的Python进程${NC}"
fi

# 关闭前端服务
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${YELLOW}正在关闭前端开发服务器 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        sleep 2
        
        # 验证进程是否已关闭
        if ! ps -p $FRONTEND_PID > /dev/null; then
            echo -e "${GREEN}✓ 前端开发服务器已成功关闭${NC}"
            rm frontend.pid
        else
            echo -e "${RED}无法正常关闭前端服务，尝试强制终止...${NC}"
            kill -9 $FRONTEND_PID
            sleep 1
            echo -e "${YELLOW}已强制终止前端服务${NC}"
            rm frontend.pid
        fi
    else
        echo -e "${YELLOW}前端PID文件中的进程 ($FRONTEND_PID) 不存在${NC}"
        rm frontend.pid
    fi
fi

# 检查是否有相关的Python进程
PYTHON_PROCESSES=$(ps aux | grep "run_v2.py" | grep -v grep | awk '{print $2}')
if [ -n "$PYTHON_PROCESSES" ]; then
    echo -e "${YELLOW}发现与run_v2.py相关的进程，正在关闭...${NC}"
    for pid in $PYTHON_PROCESSES; do
        echo -e "${BLUE}关闭进程 $pid...${NC}"
        kill $pid
    done
    
    # 验证进程是否已关闭
    sleep 2
    if [ -z "$(ps aux | grep 'run_v2.py' | grep -v grep)" ]; then
        echo -e "${GREEN}✓ 所有相关Python进程已关闭${NC}"
    else
        echo -e "${RED}某些进程无法正常关闭，尝试强制终止...${NC}"
        for pid in $PYTHON_PROCESSES; do
            kill -9 $pid 2>/dev/null
        done
        echo -e "${YELLOW}已强制终止所有进程${NC}"
    fi
fi

echo -e "${GREEN}===== 关闭完成 =====${NC}"
echo -e "${BLUE}所有青蛙AI相关服务已关闭${NC}" 