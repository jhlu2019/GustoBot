"""
启动 GustoBot 聊天系统

同时启动后端 API 服务器和提供前端页面访问
"""
import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_backend():
    """启动后端 FastAPI 服务器"""
    print("🚀 启动后端服务器...")

    # 检查环境变量
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  警告: 未设置 OPENAI_API_KEY 环境变量")
        print("请确保在 .env 文件中配置了 OPENAI_API_KEY")

    # 启动 uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn",
        "gustobot.main:application",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]

    subprocess.run(cmd, cwd=project_root)

def start_frontend():
    """启动前端静态文件服务器"""
    print("🌐 启动前端服务器...")

    # 使用 Python 内置的 HTTP 服务器
    import http.server
    import socketserver

    os.chdir(project_root / "web")

    class Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # 添加 CORS 头
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', '*')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()

    with socketserver.TCPServer(("", 8001), Handler) as httpd:
        print(f"前端服务器运行在: http://localhost:8001")
        httpd.serve_forever()

def open_browser():
    """打开浏览器"""
    time.sleep(3)  # 等待服务器启动
    webbrowser.open("http://localhost:8001/chatbot/")

def main():
    """主函数"""
    print("="*60)
    print("🤖 GustoBot 智能菜谱助手")
    print("="*60)
    print("\n正在启动服务...\n")

    # 在新线程中启动后端
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # 等待后端启动
    time.sleep(2)

    # 在新线程中启动前端
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()

    # 打开浏览器
    open_browser()

    print("\n" + "="*60)
    print("✅ 服务已启动!")
    print("\n访问地址:")
    print("  • 前端界面: http://localhost:8001/chatbot/")
    print("  • API 文档: http://localhost:8000/docs")
    print("\n使用说明:")
    print("  1. 在浏览器中打开前端界面")
    print("  2. 可以选择全屏模式或右下角小部件")
    print("  3. 输入问题，系统会自动路由并回复")
    print("\n按 Ctrl+C 停止服务")
    print("="*60)

    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 正在停止服务...")
        sys.exit(0)

if __name__ == "__main__":
    main()