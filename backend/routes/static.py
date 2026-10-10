"""前端静态文件（含 SPA fallback）"""

import os
import sys
from flask import Blueprint, jsonify, send_from_directory

bp = Blueprint("static", __name__)


def _resource_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


FRONTEND_DIR = os.path.join(_resource_dir(), "frontend_dist")


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not Found"}), 404
    full = os.path.join(FRONTEND_DIR, path)
    if path and os.path.exists(full):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")
