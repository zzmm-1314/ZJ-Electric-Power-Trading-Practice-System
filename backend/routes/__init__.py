"""注册所有蓝图"""

from .exam import bp as exam_bp
from .manage import bp as manage_bp
from .paper import bp as paper_bp
from .knowledge import bp as knowledge_bp
from .settings import bp as settings_bp
from .ai_config import bp as ai_config_bp
from .db_config import bp as db_config_bp
from .static import bp as static_bp


def register_blueprints(app):
    app.register_blueprint(exam_bp)
    app.register_blueprint(manage_bp)
    app.register_blueprint(paper_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(ai_config_bp)
    app.register_blueprint(db_config_bp)
    # 静态文件放最后，作为兜底
    app.register_blueprint(static_bp)
