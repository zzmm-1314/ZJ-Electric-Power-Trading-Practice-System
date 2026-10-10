"""主入口：初始化、注册蓝图、启动服务"""

import atexit
import socket
import sys
import threading
import time
import webbrowser

import jieba
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS

from data_manager import init_db, clean_old_progress
from routes import register_blueprints

# ---------- 初始化 ----------
jieba.initialize()
print("jieba 分词器初始化完成", file=sys.stderr)

app = Flask(__name__)
CORS(app)
init_db()
print("数据库初始化完成", file=sys.stderr)

# 启动时清理过期已答记录
try:
    print("🔍 启动清理：扫描数据库中的过期已答记录...", file=sys.stderr)
    clean_old_progress()
except Exception as e:
    print(f"⚠️ 启动清理失败（不影响应用启动）: {e}", file=sys.stderr)

# 注册所有蓝图
register_blueprints(app)
print("所有路由已注册", file=sys.stderr)

# ---------- 定时任务 ----------
scheduler = BackgroundScheduler()
scheduler.add_job(func=clean_old_progress, trigger="cron", hour=2, minute=0)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


# ---------- 启动辅助 ----------
def _find_free_port(start: int = 5000) -> int:
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


def _open_browser(url: str, delay: float = 1.5):
    time.sleep(delay)
    webbrowser.open(url)


if __name__ == "__main__":
    port = _find_free_port(5000)
    url = f"http://127.0.0.1:{port}"
    print(f"🚀 服务启动: {url}", file=sys.stderr)

    threading.Thread(target=_open_browser, args=(url, 1.5), daemon=True).start()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
