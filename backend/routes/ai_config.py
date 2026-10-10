"""AI 配置 + 对话路由"""

import sys
from flask import Blueprint, jsonify, request

from ai_client import AIClient, get_active_ai_client
from data_manager import (
    get_ai_config,
    get_ai_provider_presets,
    get_active_ai_provider,
    add_ai_provider,
    update_ai_provider,
    delete_ai_provider,
    set_active_ai_provider,
    AI_PROVIDER_PRESETS,
)

bp = Blueprint("ai_config", __name__, url_prefix="/api/ai_config")


@bp.route("", methods=["GET"])
def get_ai_config_route():
    return jsonify(get_ai_config(mask_key=True))


@bp.route("/presets", methods=["GET"])
def get_ai_presets_route():
    return jsonify(get_ai_provider_presets())


@bp.route("/providers", methods=["POST"])
def add_ai_provider_route():
    data = request.json or {}
    if not data.get("name"):
        return jsonify({"error": "名称不能为空"}), 400
    if not data.get("api_key"):
        return jsonify({"error": "API Key 不能为空"}), 400

    ptype = (data.get("provider") or "zhipu").strip()
    sdk = data.get("sdk") or next(
        (p["sdk"] for p in AI_PROVIDER_PRESETS if p["type"] == ptype),
        "openai",
    )

    provider = {
        "name": data["name"].strip(),
        "provider": ptype,
        "sdk": sdk,
        "api_key": data["api_key"].strip(),
        "model": (data.get("model") or "").strip(),
        "base_url": (data.get("base_url") or "").strip(),
        "retry_count": int(data.get("retry_count", 7)),
        "retry_delay": int(data.get("retry_delay", 2)),
    }
    try:
        add_ai_provider(provider)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/providers/<provider_id>", methods=["PUT"])
def update_ai_provider_route(provider_id):
    data = request.json or {}
    allowed = {
        "name",
        "provider",
        "sdk",
        "api_key",
        "model",
        "base_url",
        "retry_count",
        "retry_delay",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    for k in ("retry_count", "retry_delay"):
        if k in updates and updates[k] is not None and updates[k] != "":
            try:
                updates[k] = int(updates[k])
            except ValueError:
                updates.pop(k)
    try:
        update_ai_provider(provider_id, updates)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/providers/<provider_id>", methods=["DELETE"])
def delete_ai_provider_route(provider_id):
    try:
        delete_ai_provider(provider_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/active", methods=["POST"])
def set_active_ai_route():
    data = request.json or {}
    provider_id = data.get("id")
    if not provider_id:
        return jsonify({"error": "缺少 provider id"}), 400
    try:
        set_active_ai_provider(provider_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/test", methods=["POST"])
def test_ai_config():
    data = request.json or {}
    provider_id = data.get("id")

    if provider_id:
        cfg = get_ai_config(mask_key=False)
        provider = next(
            (p for p in cfg["providers"] if p.get("id") == provider_id), None
        )
        if not provider:
            return jsonify({"success": False, "error": "Provider 不存在"}), 404
        if data.get("api_key"):
            provider = {**provider, "api_key": data["api_key"]}
    else:
        provider = get_active_ai_provider()

    if not provider or not provider.get("api_key"):
        return jsonify({"success": False, "error": "缺少 API Key"}), 400

    try:
        ai = AIClient(provider)
        reply = ai.chat(
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=16,
            temperature=0.2,
        )
        return jsonify({"success": True, "reply": (reply or "")[:80]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ---------- AI 对话（不在 /ai_config 前缀下，放在这里方便管理） ----------
chat_bp = Blueprint("chat", __name__, url_prefix="/api")


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    try:
        ai = get_active_ai_client()
        reply = ai.chat(
            messages=[
                {
                    "role": "system",
                    "content": "你是一个学习助手，帮助用户解答学习问题。",
                },
                {"role": "user", "content": user_message},
            ],
            max_tokens=4096,
            temperature=0.7,
        )
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"AI 对话失败: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500
