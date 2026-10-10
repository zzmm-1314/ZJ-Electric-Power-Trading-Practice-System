"""数据库配置路由"""

import sys
from flask import Blueprint, jsonify, request

from state import state
from data_manager import (
    get_db,
    get_db_config,
    save_db_config,
    init_db,
    DB_CONFIG_FILE,
)

bp = Blueprint("db_config", __name__, url_prefix="/api/db_config")


@bp.route("", methods=["GET"])
def get_db_config_route():
    cfg = get_db_config()
    has_pwd = bool(cfg.get("password"))
    masked = dict(cfg)
    if has_pwd:
        masked["password"] = "*" * min(len(cfg["password"]), 12)
    masked["has_password"] = has_pwd
    masked["config_file"] = DB_CONFIG_FILE
    return jsonify(masked)


@bp.route("/test", methods=["POST"])
def test_db_config():
    data = request.json or {}
    current = get_db_config()

    pwd = data.get("password")
    if pwd is None or (pwd and set(pwd) == {"*"}):
        pwd = current.get("password", "")

    test_cfg = {
        "host": data.get("host", current["host"]),
        "user": data.get("user", current["user"]),
        "password": pwd,
        "database": data.get("database", current["database"]),
        "port": int(data.get("port", current["port"])),
    }
    try:
        conn = get_db(override=test_cfg)
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@bp.route("", methods=["POST"])
def save_db_config_route():
    data = request.json or {}
    current = get_db_config()

    pwd = data.get("password")
    if pwd is None or (pwd and set(pwd) == {"*"}):
        pwd = current.get("password", "")

    new_cfg = {
        "host": (data.get("host") or current["host"]).strip(),
        "user": (data.get("user") or current["user"]).strip(),
        "password": pwd,
        "database": (data.get("database") or current["database"]).strip(),
        "port": int(data.get("port") or current["port"]),
    }

    try:
        conn = get_db(override=new_cfg)
        conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": f"连接失败：{e}"}), 400

    save_db_config(new_cfg)

    try:
        init_db()
        state.reload_questions()
    except Exception as e:
        print(f"配置保存后重载失败（不影响下次启动）: {e}", file=sys.stderr)

    return jsonify({"success": True, "message": "配置已保存并生效"})
