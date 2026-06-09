"""
使用ngrok运行Streamlit应用，使其可以从外网访问
"""
import subprocess
import time
import threading
from pyngrok import ngrok
import os

def start_streamlit():
    """启动Streamlit应用"""
    subprocess.run([
        "streamlit", "run", "app.py", 
        "--server.address", "0.0.0.0", 
        "--server.port", "8501"
    ])

def main():
    # 设置ngrok认证令牌（如果您有账户的话）
    # ngrok.set_auth_token("YOUR_AUTH_TOKEN_HERE")  # 如果您有ngrok账户，取消注释并替换为您的令牌
    
    # 在单独的线程中启动Streamlit服务器
    streamlit_thread = threading.Thread(target=start_streamlit)
    streamlit_thread.daemon = True
    streamlit_thread.start()
    
    # 等待Streamlit服务器启动
    time.sleep(3)
    
    # 创建ngrok隧道
    public_url = ngrok.connect(8501, "http")
    print(f"Streamlit应用可通过以下地址从外网访问: {public_url}")
    print("按 Ctrl+C 停止服务")
    
    try:
        # 保持程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n关闭隧道...")
        ngrok.disconnect(public_url.public_url)
        ngrok.kill()

if __name__ == "__main__":
    main()