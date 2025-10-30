#!/bin/bash

# GustoBot 开发环境启动脚本

echo "🍳 GustoBot 智能菜谱助手"
echo "=========================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 选择启动方式
echo "请选择启动方式："
echo "1) Docker Compose (推荐)"
echo "2) 本地开发"
echo "3) 仅后端"
echo "4) 仅前端"
echo ""
read -p "请输入选择 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🐳 使用 Docker Compose 启动所有服务..."
        echo ""

        # 检查 .env 文件
        if [ ! -f .env ]; then
            echo "⚠️  .env 文件不存在，创建示例文件..."
            cp .env.example .env 2>/dev/null || echo "请手动创建 .env 文件"
        fi

        # 启动服务
        docker-compose -f docker-compose.dev.yml up -d

        echo ""
        echo "✅ 服务启动成功！"
        echo ""
        echo "访问地址："
        echo "  • 前端: http://localhost:3000"
        echo "  • 后端: http://localhost:8000"
        echo "  • API文档: http://localhost:8000/docs"
        echo ""
        echo "查看日志: docker-compose -f docker-compose.dev.yml logs -f"
        echo "停止服务: docker-compose -f docker-compose.dev.yml down"
        ;;

    2)
        echo ""
        echo "💻 本地开发模式..."
        echo ""

        # 启动后端
        echo "启动后端..."
        cd gustobot || exit 1
        if [ ! -d "venv" ]; then
            echo "创建虚拟环境..."
            python -m venv venv
        fi

        # 激活虚拟环境
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
            source venv/Scripts/activate
        else
            source venv/bin/activate
        fi

        pip install -r requirements.txt

        # 后台启动后端
        python run.py start &
        BACKEND_PID=$!

        cd ..

        # 启动前端
        echo "启动前端..."
        cd web

        if [ ! -d "node_modules" ]; then
            echo "安装前端依赖..."
            npm install
        fi

        npm run dev &
        FRONTEND_PID=$!

        echo ""
        echo "✅ 服务启动成功！"
        echo ""
        echo "访问地址："
        echo "  • 前端: http://localhost:3000"
        echo "  • 后端: http://localhost:8000"
        echo ""
        echo "按 Ctrl+C 停止所有服务"

        # 等待信号
        trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
        wait
        ;;

    3)
        echo ""
        echo "🔧 仅启动后端..."
        echo ""

        cd gustobot || exit 1
        if [ ! -d "venv" ]; then
            python -m venv venv
        fi

        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
            source venv/Scripts/activate
        else
            source venv/bin/activate
        fi

        pip install -r requirements.txt
        python run.py start
        ;;

    4)
        echo ""
        echo "🎨 仅启动前端..."
        echo ""

        cd web || exit 1
        if [ ! -d "node_modules" ]; then
            npm install
        fi

        npm run dev
        ;;

    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac