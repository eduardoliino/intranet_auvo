from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from datetime import datetime


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


login_manager.login_message = None
login_manager.login_message_category = "info"


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-forte-e-diferente'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///intranet.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y %H:%M'):
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return value
        if isinstance(value, datetime):
            return value.strftime(format)
        return value

    @app.context_processor
    def inject_global_vars():
        from .models import Colaborador, Ouvidoria
        total_colaboradores = Colaborador.query.count()

        tem_nova_ouvidoria = False
        if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
            tem_nova_ouvidoria = db.session.query(
                Ouvidoria.query.filter_by(status='Nova').exists()).scalar()

        return dict(
            total_colaboradores=total_colaboradores,
            tem_nova_ouvidoria=tem_nova_ouvidoria
        )

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .admin_routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .colaborador_routes import colaborador_bp
    app.register_blueprint(colaborador_bp)

    return app
