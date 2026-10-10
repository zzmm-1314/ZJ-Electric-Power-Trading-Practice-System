"""题目管理路由"""

from flask import Blueprint, jsonify, request

from state import state
from data_manager import (
    get_questions_page,
    create_question_in_db,
    update_question,
    delete_question,
    batch_delete_questions,
    set_question_knowledge,
    reset_all_ids,
    get_question_knowledge,
    import_from_json_data,
)

bp = Blueprint("manage", __name__, url_prefix="/api/manage")


@bp.route("/list", methods=["GET"])
def manage_list():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "")
    wrong_only = request.args.get("wrong_only", "false").lower() == "true"
    qtype = request.args.get("type", "")
    unanswered_only = request.args.get("unanswered_only", "false").lower() == "true"
    paper_id = request.args.get("paper_id", type=int)

    questions, total = get_questions_page(
        search,
        page,
        per_page,
        wrong_only,
        qtype,
        unanswered_only,
        paper_id,
    )
    return jsonify(
        {"items": questions, "total": total, "page": page, "per_page": per_page}
    )


@bp.route("/create", methods=["POST"])
def create_question():
    data = request.get_json()
    force = data.pop("force", False)
    knowledge_ids = data.get("knowledge_ids", [])

    if force:
        qid = create_question_in_db(data, threshold=1.1)  # 阈值调高即跳过检测
        if knowledge_ids:
            set_question_knowledge(qid, knowledge_ids)
        state.reload_questions()
        reset_all_ids()
        state.reload_questions()
        return jsonify({"id": qid, "success": True})

    qid, is_dup, existing_id, similarity = create_question_in_db(data)
    if is_dup:
        return (
            jsonify(
                {
                    "success": False,
                    "duplicate": True,
                    "existing_id": existing_id,
                    "similarity": round(similarity * 100, 1),
                    "error": f"与已有题目 #{existing_id} 高度相似（{similarity*100:.1f}%），已跳过",
                }
            ),
            409,
        )

    if knowledge_ids:
        set_question_knowledge(qid, knowledge_ids)
    state.reload_questions()
    reset_all_ids()
    state.reload_questions()
    return jsonify({"id": qid, "success": True})


@bp.route("/edit/<int:qid>", methods=["PUT"])
def edit_question(qid):
    data = request.get_json()
    knowledge_ids = data.get("knowledge_ids", [])
    success, error, existing_id = update_question(qid, data)
    if not success:
        return (
            jsonify(
                {
                    "success": False,
                    "duplicate": True,
                    "existing_id": existing_id,
                    "error": error,
                }
            ),
            409,
        )
    set_question_knowledge(qid, knowledge_ids)
    state.reload_questions()
    return jsonify({"success": True})


@bp.route("/delete/<int:qid>", methods=["DELETE"])
def delete_question_route(qid):
    delete_question(qid)
    state.reload_questions()
    reset_all_ids()
    state.reload_questions()
    return jsonify({"success": True})


@bp.route("/batch_delete", methods=["POST"])
def batch_delete():
    data = request.get_json()
    ids = data.get("ids", [])
    if not ids:
        return jsonify({"error": "未提供ID"}), 400
    batch_delete_questions(ids)
    state.reload_questions()
    reset_all_ids()
    state.reload_questions()
    return jsonify({"success": True})
