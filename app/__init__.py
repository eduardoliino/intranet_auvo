# app/__init__.py

from flask import Flask


def create_app():
    # Cria a instância da aplicação
    app = Flask(__name__)

    # Registra o nosso Blueprint na aplicação
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Retorna a aplicação configurada
    return app
