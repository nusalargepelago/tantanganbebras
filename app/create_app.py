"""Application factory for Minimals."""
from __future__ import annotations

import os

from flask import Flask

from app.config import Config
from app.infra.api_key_auth import init_api_key_auth
from app.infra.rate_limit import init_rate_limiter
from app.infra.security import init_talisman
from framework.extensions import cors, csrf, db, init_proxy, login, migrate
from framework.infra.errors import register_error_handlers
from framework.infra.frontend import register_spa
from framework.infra.migrations import migrations_enabled, run_migrations
from framework.logging import init_logging, request_middleware


def _init_cors(app: Flask) -> None:
    origins = app.config["CORS_ORIGINS"]
    if not origins:
        return

    if "*" in origins:
        raise ValueError(
            "CORS_ORIGINS='*' is not allowed: with credentials enabled "
            "flask-cors would echo any Origin. List explicit origins."
        )

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"],
        allow_headers=["Content-Type", "X-CSRFToken", "X-Requested-With"],
        expose_headers=["Content-Type"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=3600,
    )


def _init_login(app: Flask) -> None:
    login.init_app(app)

    from framework.api.response import error

    @login.unauthorized_handler
    def _unauthorized():
        return error("unauthorized", 401)

    from app.infra.security_manager import load_user

    login.user_loader(load_user)


def _init_csrf(app: Flask) -> None:
    if not app.config["WTF_CSRF_ENABLED"]:
        return

    csrf.init_app(app)

    from app.infra.api import bp as app_api_bp
    from app.infra.csrf import bp as csrf_bp
    from app.infra.health import bp as health_bp

    csrf.exempt(app_api_bp._bp)
    csrf.exempt(csrf_bp._bp)
    csrf.exempt(health_bp)


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=Config.STATIC_FOLDER,
        static_url_path="/static",
    )
    app.config.from_object(Config)

    init_proxy(app)
    init_logging(app)

    db.init_app(app)
    migrate.init_app(
        app, db, directory=os.path.join(app.root_path, "migrations")
    )
    _init_login(app)
    _init_csrf(app)
    _init_cors(app)
    init_talisman(app)
    init_rate_limiter(app)
    init_api_key_auth(app)

    with app.app_context():
        # Must precede ensure_member_role(): seeding checks that the roles table
        # exists, so on a fresh database it would silently skip without this.
        if migrations_enabled():
            run_migrations(app)

        from app.account.models import ApiKey  # noqa: F401
        from app.auth.models import Role, User, user_roles  # noqa: F401
        from app.event.models import Event, EventAttempt  # noqa: F401
        from app.infra.audit import AuditLog  # noqa: F401
        from app.infra.models import AppSetting  # noqa: F401
        from app.infra.roles import ensure_member_role
        from app.practice.models import Practice  # noqa: F401
        from app.question.models import Question  # noqa: F401
        from app.student.models import Student  # noqa: F401
        from app.todos.models import Todo  # noqa: F401
        from app.topic.models import Topic  # noqa: F401

        ensure_member_role()

        from app.account import bp as account_bp
        from app.account.api_key_api import bp as account_api_key_bp
        from app.auth import bp as auth_bp
        from app.dashboard import bp as dashboard_bp
        from app.event import bp as event_bp
        from app.event import event_student_bp
        from app.infra.api import bp as app_api_bp
        from app.infra.backup import bp as backup_bp
        from app.infra.csrf import bp as csrf_bp
        from app.infra.health import bp as health_bp
        from app.infra.seo import bp as seo_bp
        from app.infra.seo import index_context
        from app.infra.setup import bp as setup_bp
        from app.infra.uploads import bp as uploads_bp
        from app.practice import bp as practice_bp
        from app.practice import staff_bp as practice_staff_bp
        from app.question import bp as question_bp
        from app.student import bp as student_bp
        from app.student import student_auth_bp, student_dashboard_bp, student_import_bp
        from app.todos import bp as todos_bp
        from app.topic import bp as topic_bp

        app.register_blueprint(health_bp)
        app.register_blueprint(csrf_bp)
        app.register_blueprint(setup_bp)
        app.register_blueprint(seo_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(account_bp)
        app.register_blueprint(account_api_key_bp)
        app.register_blueprint(app_api_bp)
        app.register_blueprint(topic_bp)
        app.register_blueprint(question_bp)
        app.register_blueprint(practice_bp)
        app.register_blueprint(practice_staff_bp)
        app.register_blueprint(event_bp)
        app.register_blueprint(event_student_bp)
        app.register_blueprint(student_bp)
        app.register_blueprint(student_auth_bp)
        app.register_blueprint(student_dashboard_bp)
        app.register_blueprint(student_import_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(todos_bp)
        app.register_blueprint(uploads_bp)
        app.register_blueprint(backup_bp)

        register_spa(
            app,
            Config.SPA_STATIC_ROOT,
            Config.SPA_URL_PREFIX,
            index_context=index_context,
        )

        register_error_handlers(app)

    request_middleware(app)

    return app
