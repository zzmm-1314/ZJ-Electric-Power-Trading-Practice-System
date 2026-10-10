"""知识点 / 知识图谱 / 图谱漫游路由"""

from flask import Blueprint, jsonify, request

from data_manager import (
    get_all_knowledge_points,
    create_knowledge_point,
    update_knowledge_point,
    delete_knowledge_point,
    get_question_knowledge,
    get_knowledge_graph_data,
    start_graph_walk,
    get_related_knowledge,
    get_recommended_next,
)

bp = Blueprint("knowledge", __name__, url_prefix="/api")


# ---------- 知识点 CRUD ----------
@bp.route("/knowledge_points", methods=["GET"])
def list_knowledge_points():
    return jsonify(get_all_knowledge_points())


@bp.route("/knowledge_points", methods=["POST"])
def add_knowledge_point():
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "知识点名称不能为空"}), 400
    kp_id = create_knowledge_point(name, data.get("description", ""))
    return jsonify({"id": kp_id, "name": name})


@bp.route("/knowledge_points/<int:kp_id>", methods=["PUT"])
def edit_knowledge_point(kp_id):
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "知识点名称不能为空"}), 400
    update_knowledge_point(kp_id, name, data.get("description", ""))
    return jsonify({"status": "ok"})


@bp.route("/knowledge_points/<int:kp_id>", methods=["DELETE"])
def remove_knowledge_point(kp_id):
    delete_knowledge_point(kp_id)
    return jsonify({"status": "ok"})


@bp.route("/question_knowledge/<int:qid>", methods=["GET"])
def question_knowledge(qid):
    return jsonify(get_question_knowledge(qid))


# ---------- 知识图谱 ----------
@bp.route("/knowledge_graph", methods=["GET"])
def knowledge_graph():
    paper_id = request.args.get("paper_id", type=int)
    data = get_knowledge_graph_data(1, paper_id)
    return jsonify(data)


@bp.route("/knowledge_points/by_paper", methods=["GET"])
def knowledge_points_by_paper():
    paper_id = request.args.get("paper_id", type=int)
    walkable = request.args.get("walkable", "false").lower() == "true"
    min_cooccur = request.args.get("min_cooccur", 1, type=int)

    data = get_knowledge_graph_data(1, paper_id)
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if walkable:
        cooccur_strength = {}
        for e in edges:
            w = e.get("weight", 0) or 0
            for key in ("source", "target"):
                if e.get(key) is not None:
                    cooccur_strength[e[key]] = max(cooccur_strength.get(e[key], 0), w)
        kps = [
            {"id": n["id"], "name": n["name"]}
            for n in nodes
            if cooccur_strength.get(n["id"], 0) >= min_cooccur
        ]
    else:
        kps = [{"id": n["id"], "name": n["name"]} for n in nodes]

    return jsonify(kps)


# ---------- 图谱漫游 ----------
@bp.route("/graph/walk/start", methods=["POST"])
def graph_walk_start():
    data = request.json
    knowledge_id = data.get("knowledge_id")
    if not knowledge_id:
        return jsonify({"error": "缺少知识点ID"}), 400
    walk_id = start_graph_walk(knowledge_id)
    return jsonify({"walk_id": walk_id})


@bp.route("/graph/walk/related", methods=["GET"])
def graph_walk_related():
    knowledge_id = request.args.get("knowledge_id", type=int)
    paper_id = request.args.get("paper_id", type=int)
    if not knowledge_id:
        return jsonify({"error": "缺少知识点ID"}), 400
    return jsonify(get_related_knowledge(knowledge_id, paper_id))


@bp.route("/graph/walk/recommend", methods=["GET"])
def graph_walk_recommend():
    knowledge_id = request.args.get("knowledge_id", type=int)
    paper_id = request.args.get("paper_id", type=int)
    limit = request.args.get("limit", 5, type=int)
    if not knowledge_id:
        return jsonify({"error": "缺少知识点ID"}), 400
    return jsonify(get_recommended_next(knowledge_id, paper_id, limit))
