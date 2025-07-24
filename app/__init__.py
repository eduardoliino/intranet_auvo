# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# --- Etapa 1: Criar as extensões ---
# As extensões são criadas aqui fora, sem estarem ligadas a nenhuma app ainda.
# Elas ficam prontas para serem importadas por outros arquivos (como models.py).
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "info"

# --- Etapa 2: A Fábrica de Aplicação ---
# Esta função monta e retorna a aplicação Flask.


def create_app():
    app = Flask(__name__)

    # Configurações essenciais da aplicação
    app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-forte-e-diferente'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///intranet.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Conecta as extensões com a instância da aplicação
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- Registrando os Blueprints (conjuntos de rotas) ---
    # É crucial que os imports sejam feitos aqui DENTRO da função.
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .admin_routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    return app
