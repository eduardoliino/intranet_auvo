# app/models.py

# 1. Importe o 'login_manager' junto com o 'db'
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

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

    # ---- ALTERE A LINHA ABAIXO ----
    imagem_filename = db.Column(db.String(120), nullable=True)
    # -------------------------------

    # Chave estrangeira para ligar o destaque a um colaborador
    colaborador_id = db.Column(db.Integer, db.ForeignKey(
        'colaborador.id'), nullable=False)
    # Relação para aceder facilmente aos dados do colaborador a partir de um destaque
    colaborador = db.relationship('Colaborador', backref='destaques')

class FaqCategoria(db.Model):
    __tablename__ = 'faq_categoria'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)

    # Relação para aceder facilmente às perguntas de uma categoria
    perguntas = db.relationship(
        'FaqPergunta', backref='categoria', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<FaqCategoria {self.nome}>'


class FaqPergunta(db.Model):
    __tablename__ = 'faq_pergunta'
    id = db.Column(db.Integer, primary_key=True)
    pergunta = db.Column(db.String(255), nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(300), nullable=True)
    link_texto = db.Column(db.String(100), nullable=True)

    # Armazenaremos as palavras-chave como um texto separado por vírgulas
    palavras_chave = db.Column(db.String(255), nullable=True)

    # Chave estrangeira para ligar a pergunta a uma categoria
    categoria_id = db.Column(db.Integer, db.ForeignKey(
        'faq_categoria.id'), nullable=False)

    def __repr__(self):
        return f'<FaqPergunta {self.pergunta[:30]}>'


class Ouvidoria(db.Model):
    __tablename__ = 'tbOuvidoria'
    id = db.Column(db.Integer, primary_key=True)
    data_envio = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    tipo_denuncia = db.Column(db.String(100), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    anonima = db.Column(db.Boolean, default=True, nullable=False)
    nome = db.Column(db.String(150), nullable=True)
    contato = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), nullable=False,
                       default='Nova') 
    responsavel = db.Column(db.String(150), nullable=True)

    def __repr__(self):
        return f'<Ouvidoria {self.id} - {self.tipo_denuncia}>'
