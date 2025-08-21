from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def get_id(self):
        return f"admin-{self.id}"

    @property
    def is_admin(self):
        return True

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Departamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    cor = db.Column(db.String(20), nullable=True, default='#7A28B8')
    colaboradores = db.relationship(
        'Colaborador', backref='departamento', lazy=True)


class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    colaboradores = db.relationship('Colaborador', backref='cargo', lazy=True)


class Colaborador(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String(100), nullable=False)
    email_corporativo = db.Column(
        db.String(120), unique=True, nullable=False, index=True)
    data_nascimento = db.Column(db.Date, nullable=False)
    data_inicio = db.Column(db.Date, nullable=True)
    password_hash = db.Column(db.String(256))
    foto_filename = db.Column(db.String(120), nullable=True)

    superior_id = db.Column(db.Integer, db.ForeignKey('colaborador.id'))
    superior = db.relationship('Colaborador', remote_side=[
                               id], backref='subordinados')

    cargo_id = db.Column(db.Integer, db.ForeignKey('cargo.id'), nullable=True)
    departamento_id = db.Column(
        db.Integer, db.ForeignKey('departamento.id'), nullable=True)

    def get_id(self):
        return f"colaborador-{self.id}"

    @property
    def is_admin(self):
        return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Aviso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(length=200), nullable=True)
    link_texto = db.Column(db.String(length=100), nullable=True)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'titulo': self.titulo, 'conteudo': self.conteudo, 'link_url': self.link_url, 'link_texto': self.link_texto, 'data_criacao_iso': self.data_criacao.isoformat() if self.data_criacao else None, 'data_criacao_fmt': self.data_criacao.strftime('%d/%m') if self.data_criacao else None}


class Destaque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    imagem_filename = db.Column(db.String(120), nullable=True)
    colaborador_id = db.Column(db.Integer, db.ForeignKey(
        'colaborador.id'), nullable=False)
    colaborador = db.relationship('Colaborador', backref='destaques')


class FaqCategoria(db.Model):
    __tablename__ = 'faq_categoria'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    perguntas = db.relationship(
        'FaqPergunta', backref='categoria', lazy=True, cascade="all, delete-orphan")


class FaqPergunta(db.Model):
    __tablename__ = 'faq_pergunta'
    id = db.Column(db.Integer, primary_key=True)
    pergunta = db.Column(db.String(255), nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(300), nullable=True)
    link_texto = db.Column(db.String(100), nullable=True)
    palavras_chave = db.Column(db.String(255), nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey(
        'faq_categoria.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'pergunta': self.pergunta,
            'resposta': self.resposta,
            'link_url': self.link_url,
            'link_texto': self.link_texto,
            'palavras_chave': self.palavras_chave,
            'categoria_id': self.categoria_id
        }


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
    status = db.Column(db.String(50), nullable=False, default='Nova')
    responsavel = db.Column(db.String(150), nullable=True)


class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    color = db.Column(db.String(20), nullable=True, default='#3788d8')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start': self.start.isoformat(),
            'end': self.end.isoformat() if self.end else None,
            'location': self.location,
            'color': self.color
        }


class ConfigLink(db.Model):
    __tablename__ = 'config_link'
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.String(300), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    """Carrega o utilizador correto com base no prefixo do ID."""
    if user_id.startswith('admin-'):
        return User.query.get(int(user_id.split('-')[1]))
    elif user_id.startswith('colaborador-'):
        return Colaborador.query.get(int(user_id.split('-')[1]))
    return None
