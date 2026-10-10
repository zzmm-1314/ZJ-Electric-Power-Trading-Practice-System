"""做题相关路由"""

import sys
from flask import Blueprint, jsonify, request

from state import state
from data_manager import (
    remove_wrong_question,
    add_wrong_question,
    update_progress_timestamp,
    get_wrong_question_ids,
)

bp = Blueprint("exam", __name__, url_prefix="/api")


@bp.route("/test", methods=["GET"])
def test():
    return jsonify({"status": "ok"})


@bp.route("/questions", methods=["GET"])
def get_questions():
    if not state.order_list:
        return jsonify(
            {
                "current_pos": 0,
                "total_display": 0,
                "total_all": state.total,
                "is_wrong": False,
                "all_done": not state.filter_wrong,
            }
        )

    if state.current_pos >= len(state.order_list):
        state.current_pos = 0
        state.save_progress()

    idx = state.order_list[state.current_pos]
    q = state.questions[idx]
    data = state.get_question_data(idx)
    data["current_pos"] = state.current_pos
    data["total_display"] = len(state.order_list)
    data["total_all"] = state.total
    data["is_wrong"] = q["id"] in state.wrong_ids
    return jsonify(data)


@bp.route("/submit", methods=["POST"])
def submit_answer():
    data = request.json
    question_id = data.get("index")
    user_ans = data.get("answer")
    if question_id is None:
        return jsonify({"error": "缺少题目id"}), 400

    target_idx = None
    for i, q in enumerate(state.questions):
        if q["id"] == question_id:
            target_idx = i
            break
    if target_idx is None:
        return jsonify({"error": "题目不存在"}), 400

    q = state.questions[target_idx]
    q_type = q["type"]
    correct_ans = q["answer"]

    if q_type == "single_choice":
        is_correct = user_ans == correct_ans
    elif q_type == "multiple_choice":
        if not isinstance(user_ans, list) or not isinstance(correct_ans, list):
            is_correct = False
        else:
            is_correct = set(user_ans) == set(correct_ans)
    elif q_type == "true_false":

        def to_bool(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.lower() == "true"
            return bool(v)

        is_correct = to_bool(user_ans) == to_bool(correct_ans)
    elif q_type in ("fill_in_blank", "calculation", "essay"):
        is_correct = user_ans.strip() == correct_ans.strip()
    else:
        is_correct = False

    if is_correct:
        remove_wrong_question(1, question_id)
    else:
        add_wrong_question(1, question_id)
    update_progress_timestamp(question_id)
    state.wrong_ids = set(get_wrong_question_ids(1))

    qid_str = str(question_id)
    if not state.progress.get(qid_str, False):
        state.progress[qid_str] = True
        state.save_progress()

    return jsonify(
        {
            "correct": is_correct,
            "correct_answer": correct_ans,
            "explanation": q.get("explanation", ""),
            "steps": q.get("steps", []),
            "is_wrong": (not is_correct) and (question_id in state.wrong_ids),
            "all_done": state.all_done,
        }
    )


@bp.route("/navigate", methods=["POST"])
def navigate():
    data = request.json
    direction = data.get("direction")
    if direction == "next":
        if state.current_pos + 1 < len(state.order_list):
            state.current_pos += 1
        else:
            return jsonify(
                {
                    "is_last": True,
                    "need_refresh": not state.filter_wrong,
                    "current_pos": state.current_pos,
                    "total_display": len(state.order_list),
                    "total_all": state.total,
                }
            )
    elif direction == "prev":
        if state.current_pos > 0:
            state.current_pos -= 1
        else:
            return jsonify({"error": "已经是第一题"}), 400
    else:
        return jsonify({"error": "无效方向"}), 400

    state.save_progress()
    result = state.current_question()
    if result is None:
        return jsonify({"error": "无题目"}), 404
    idx, q = result
    data = state.get_question_data(idx)
    data["current_pos"] = state.current_pos
    data["total_display"] = len(state.order_list)
    data["total_all"] = state.total
    data["is_wrong"] = q["id"] in state.wrong_ids
    return jsonify(data)


@bp.route("/jump", methods=["POST"])
def jump_to():
    data = request.json
    pos = data.get("pos")
    if pos is None or not isinstance(pos, int):
        return jsonify({"error": "缺少位置参数"}), 400
    if pos < 0 or pos >= len(state.order_list):
        return jsonify({"error": "位置超出范围"}), 400
    state.current_pos = pos
    state.save_progress()
    result = state.current_question()
    if result is None:
        return jsonify({"error": "无题目"}), 404
    idx, q = result
    data = state.get_question_data(idx)
    data["current_pos"] = state.current_pos
    data["total_display"] = len(state.order_list)
    data["total_all"] = state.total
    data["is_wrong"] = q["id"] in state.wrong_ids
    return jsonify(data)


@bp.route("/refresh", methods=["POST"])
def refresh_questions():
    state.rebuild_order()
    state.current_pos = 0
    state.save_progress()
    idx, q = state.current_question()
    if q is None:
        return jsonify({"error": "没有符合条件的题目"}), 404
    data = state.get_question_data(idx)
    data["current_pos"] = state.current_pos
    data["total_display"] = len(state.order_list)
    data["total_all"] = state.total
    data["is_wrong"] = q["id"] in state.wrong_ids
    return jsonify(data)


@bp.route("/answer_sheet", methods=["GET"])
def answer_sheet():
    return jsonify(state.get_answer_sheet())


@bp.route("/chop_question", methods=["POST"])
def chop_question():
    data = request.json
    question_id = data.get("index")
    if question_id is None:
        return jsonify({"error": "缺少题目id"}), 400

    target_idx = None
    for i, q in enumerate(state.questions):
        if q["id"] == question_id:
            target_idx = i
            break
    if target_idx is None:
        return jsonify({"error": "题目不存在"}), 400

    remove_wrong_question(1, question_id)
    qid_str = str(question_id)
    if not state.progress.get(qid_str, False):
        state.progress[qid_str] = True
        state.save_progress()
    state.wrong_ids = set(get_wrong_question_ids(1))
    return jsonify({"status": "ok"})


@bp.route("/reload", methods=["POST"])
def reload_questions():
    success = state.reload_questions()
    if success:
        return jsonify({"status": "ok", "total": state.total})
    return jsonify({"error": "刷新题库失败"}), 500
