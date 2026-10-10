"""全局做题状态：所有路由共享的 ExamState 单例"""

import random
import sys

from data_manager import (
    load_questions,
    load_user_settings,
    save_user_settings,
    get_wrong_question_ids,
)


class ExamState:
    def __init__(self):
        print("ExamState 初始化开始", file=sys.stderr)
        try:
            self.questions, self.paper_info = load_questions()
            self.total = len(self.questions)
            settings = load_user_settings()
            self.current_pos = settings.get("current_pos", 0)
            self.filter_wrong = settings.get("filter_wrong", False)
            self.random_order = settings.get("random_order", False)
            self.wrong_ids = set(get_wrong_question_ids(1))
            self.practice_limit = settings.get("practice_limit", 20)
            self.paper_id = settings.get("paper_id")
            self.order_list = []
            self.progress = settings.get("progress", {})
            self.progress_timestamp = settings.get("progress_timestamp", {})
            self.all_done = False
            self._build_order_list()
            print(f"ExamState 初始化成功，paper_id={self.paper_id}", file=sys.stderr)
        except Exception as e:
            print(f"ExamState 初始化失败: {e}", file=sys.stderr)
            self.questions = []
            self.paper_info = {"title": "无试卷"}
            self.total = 0
            self.current_pos = 0
            self.filter_wrong = False
            self.random_order = False
            self.wrong_ids = set()
            self.order_list = []
            self.practice_limit = 20
            self.paper_id = None
            self.progress = {}
            self.progress_timestamp = {}
            self.all_done = False

    def _build_order_list(self):
        if self.paper_id is not None:
            base_indices = [
                i
                for i, q in enumerate(self.questions)
                if q.get("paper_id") == self.paper_id
            ]
        else:
            base_indices = list(range(self.total))

        if self.filter_wrong:
            wrong_ids_str = {str(wid) for wid in self.wrong_ids}
            indices = [
                i for i in base_indices if str(self.questions[i]["id"]) in wrong_ids_str
            ]
        else:
            indices = [
                i
                for i in base_indices
                if not self.progress.get(str(self.questions[i]["id"]), False)
            ]

        if self.random_order:
            random.shuffle(indices)
        else:
            indices.sort(key=lambda idx: self.questions[idx]["id"])

        if self.practice_limit > 0 and len(indices) > self.practice_limit:
            indices = random.sample(indices, self.practice_limit)

        self.order_list = indices
        paper_total = len(base_indices)
        self.all_done = (not self.filter_wrong) and (
            len(self.order_list) == 0 and paper_total > 0
        )

    def rebuild_order(self):
        self._build_order_list()
        if self.current_pos >= len(self.order_list):
            self.current_pos = 0

    def current_question(self):
        if not self.order_list:
            return None
        if self.current_pos >= len(self.order_list):
            self.current_pos = 0
        idx = self.order_list[self.current_pos]
        return idx, self.questions[idx]

    def get_question_data(self, idx):
        q = self.questions[idx]
        return {
            "id": q["id"],
            "paper_id": q.get("paper_id"),
            "type": q["type"],
            "content": q["content"],
            "options": q.get("options", []),
            "explanation": q.get("explanation", ""),
            "steps": q.get("steps", []),
            "correct_answer": q.get("answer", ""),
            "user_answer": None,
        }

    def save_progress(self):
        save_user_settings(
            {
                "current_pos": self.current_pos,
                "filter_wrong": self.filter_wrong,
                "random_order": self.random_order,
                "practice_limit": self.practice_limit,
                "paper_id": self.paper_id,
                "progress": self.progress,
            }
        )

    def reload_questions(self):
        try:
            self.questions, self.paper_info = load_questions()
            self.total = len(self.questions)
            self.wrong_ids = set(get_wrong_question_ids(1))
            self.rebuild_order()
            self.save_progress()
            return True
        except Exception as e:
            print(f"刷新题库失败: {e}", file=sys.stderr)
            return False

    def get_answer_sheet(self):
        items = []
        wrong_ids_str = {str(wid) for wid in self.wrong_ids}
        for pos, idx in enumerate(self.order_list):
            q = self.questions[idx]
            items.append(
                {
                    "pos": pos,
                    "index": idx,
                    "id": q["id"],
                    "type": q["type"],
                    "is_wrong": str(q["id"]) in wrong_ids_str,
                }
            )
        return {
            "total": len(self.order_list),
            "items": items,
            "current_pos": self.current_pos,
        }


# 全局单例，路由直接 from state import state
state = ExamState()
