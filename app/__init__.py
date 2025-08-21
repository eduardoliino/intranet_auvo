from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_session import Session
from datetime import datetime, timedelta  # Import timedelta

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = None
login_manager.login_message_category = "info"

sess = Session()


def create_app():
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-forte-e-diferente'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///intranet.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configuração de sessão
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_THRESHOLD'] = 100
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    sess.init_app(app)

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
        if current_user.is_authenticated and current_user.tem_permissao('gerenciar_ouvidoria'):
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

    @app.cli.command('seed')
    def seed():
        from datetime import date
        from .models import Permissao, Colaborador

        permissoes_padrao = [
            'gerenciar_avisos',
            'gerenciar_destaques',
            'gerenciar_eventos',
            'gerenciar_faq',
            'gerenciar_ouvidoria',
            'gerenciar_links',
            'gerenciar_cargos_departamentos',
            'gerenciar_colaboradores',
        ]

        for nome in permissoes_padrao:
            if not Permissao.query.filter_by(nome=nome).first():
                db.session.add(Permissao(nome=nome))

        admin_email = 'rh@auvo.com.br'
        if not Colaborador.query.filter_by(email_corporativo=admin_email).first():
            admin = Colaborador(
                nome='RH',
                sobrenome='Auvo',
                email_corporativo=admin_email,
                data_nascimento=date.today(),
                data_inicio=date.today(),
                is_admin=True
            )
            admin.set_password('changeme')
            db.session.add(admin)

        db.session.commit()
        print('Seed completed')

    return app
