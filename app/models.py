# app/models.py

# 1. Importe o 'login_manager' junto com o 'db'
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# 2. Adicione esta função logo abaixo dos imports.
#    Ela conecta o Flask-Login ao seu modelo User.


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# O resto do seu código permanece exatamente igual
# --------------------------------------------------

# Modelo para o usuário administrativo (RH)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Modelo para os Colaboradores


class Colaborador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String(100), nullable=False)
    email_corporativo = db.Column(
        db.String(120), unique=True, nullable=False, index=True)
    data_nascimento = db.Column(db.Date, nullable=False)
    password_hash = db.Column(db.String(256))
    cargo = db.Column(db.String(100), nullable=True)
    time = db.Column(db.String(100), nullable=True)
    foto_filename = db.Column(db.String(120), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Modelo para os Avisos


class Aviso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(length=200), nullable=True)
    link_texto = db.Column(db.String(length=100), nullable=True)


class Destaque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)

    # Campo para guardar o nome do arquivo do certificado
    certificado_filename = db.Column(db.String(120), nullable=True)

    # Chave estrangeira para ligar o destaque a um colaborador
    colaborador_id = db.Column(db.Integer, db.ForeignKey(
        'colaborador.id'), nullable=False)
    # Relação para aceder facilmente aos dados do colaborador a partir de um destaque
    colaborador = db.relationship('Colaborador', backref='destaques')
