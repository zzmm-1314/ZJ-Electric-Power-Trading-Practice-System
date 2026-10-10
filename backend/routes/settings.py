"""设置 / 进度 / 统计 / 清理路由"""

from flask import Blueprint, jsonify, request

from state import state
from data_manager import (
    get_db,
    get_stats_data,
    get_recent_wrong_questions,
    get_wrong_report_data,
    get_daily_stats,
    reset_all_ids,
    clean_old_progress,
    clean_old_progress_with_days,
    import_from_json_data,
)

bp = Blueprint("settings", __name__, url_prefix="/api")


@bp.route("/settings", methods=["POST"])
def set_settings():
    data = request.json
    if "filter_wrong" in data:
        state.filter_wrong = data["filter_wrong"]
    if "random_order" in data:
        state.random_order = data["random_order"]
    if "limit" in data:
        state.practice_limit = data["limit"]
    if "paper_id" in data:
        state.paper_id = data["paper_id"]
        state.current_pos = 0
    state.rebuild_order()
    state.save_progress()
    return jsonify(
        {
            "status": "ok",
            "filter_wrong": state.filter_wrong,
            "random_order": state.random_order,
            "practice_limit": state.practice_limit,
            "paper_id": state.paper_id,
        }
    )


@bp.route("/user_settings", methods=["GET"])
def get_user_settings():
    return jsonify(
        {
            "filter_wrong": state.filter_wrong,
            "random_order": state.random_order,
            "practice_limit": state.practice_limit,
            "paper_id": state.paper_id,
            "current_pos": state.current_pos,
        }
    )


@bp.route("/reset_progress", methods=["POST"])
def reset_progress():
    state.progress = {}
    state.save_progress()
    state.rebuild_order()
    return jsonify({"status": "ok"})


@bp.route("/reset_all", methods=["POST"])
def reset_all():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM wrong_questions WHERE user_id = 1")
            cursor.execute("DELETE FROM user_settings WHERE user_id = 1")
        conn.commit()
    finally:
        conn.close()
    state.wrong_ids = set()
    state.current_pos = 0
    state.rebuild_order()
    state.save_progress()
    return jsonify({"status": "ok"})


@bp.route("/stats", methods=["GET"])
def get_stats():
    paper_id = request.args.get("paper_id", type=int)
    return jsonify(get_stats_data(paper_id))


@bp.route("/recent_wrong", methods=["GET"])
def recent_wrong():
    limit = request.args.get("limit", 10, type=int)
    paper_id = request.args.get("paper_id", type=int)
    return jsonify(get_recent_wrong_questions(1, limit, paper_id))


@bp.route("/wrong_report", methods=["GET"])
def wrong_report():
    paper_id = request.args.get("paper_id", type=int)
    return jsonify(get_wrong_report_data(1, paper_id))


@bp.route("/daily_stats", methods=["GET"])
def daily_stats():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    paper_id = request.args.get("paper_id", type=int)
    return jsonify(get_daily_stats(1, year, month, paper_id))


@bp.route("/clean_progress", methods=["POST"])
def clean_progress():
    data = request.json or {}
    days = data.get("days")
    if days is not None:
        try:
            days = int(days)
            if days < 1:
                days = 1
        except (TypeError, ValueError):
            return jsonify({"error": "days 参数无效"}), 400
        clean_old_progress_with_days(days)
        return jsonify({"status": "ok", "days": days})
    clean_old_progress()
    return jsonify({"status": "ok", "days": "database"})


@bp.route("/set_clean_days", methods=["POST"])
def set_clean_days():
    data = request.json
    days = data.get("days", 7)
    if days < 1:
        days = 1
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE user_settings SET clean_days = %s WHERE user_id = 1", (days,)
            )
            conn.commit()
        return jsonify({"status": "ok", "days": days})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/import", methods=["POST"])
def import_questions():
    data = request.get_json()
    if not data or "questions" not in data:
        return jsonify({"error": "无效数据"}), 400
    paper_id = data.get("paper_id")
    threshold = data.get("threshold", 0.85)
    added, skipped = import_from_json_data(data, paper_id, threshold)
    state.reload_questions()
    reset_all_ids()
    state.reload_questions()
    return jsonify({"added": added, "skipped": skipped})
