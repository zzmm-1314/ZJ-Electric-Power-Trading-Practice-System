"""试卷管理路由"""

from flask import Blueprint, jsonify, request

from state import state
from data_manager import (
    get_all_papers,
    create_paper_db,
    update_paper,
    delete_paper,
)

bp = Blueprint("paper", __name__, url_prefix="/api/papers")


@bp.route("", methods=["GET"])
def get_papers():
    return jsonify(get_all_papers())


@bp.route("", methods=["POST"])
def create_paper_route():
    data = request.json
    title = data.get("title", "未命名试卷")
    if not title:
        return jsonify({"error": "试卷名称不能为空"}), 400
    paper_id = create_paper_db(title)
    return jsonify({"id": paper_id, "title": title})


@bp.route("/<int:paper_id>", methods=["PUT"])
def update_paper_route(paper_id):
    data = request.json
    title = data.get("title")
    if not title:
        return jsonify({"error": "试卷名称不能为空"}), 400
    update_paper(paper_id, title)
    return jsonify({"status": "ok"})


@bp.route("/<int:paper_id>", methods=["DELETE"])
def delete_paper_route(paper_id):
    delete_paper(paper_id)
    state.reload_questions()
    return jsonify({"status": "ok"})
