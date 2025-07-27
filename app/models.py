from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('admin-'):
        return User.query.get(int(user_id.split('-')[1]))
    elif user_id.startswith('colaborador-'):
        return Colaborador.query.get(int(user_id.split('-')[1]))
    return None


# O resto do seu código permanece exatamente igual
# --------------------------------------------------

# Modelo para o usuário administrativo (RH)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    # --- ALTERAÇÃO 2: MÉTODO get_id() PARA ADMIN ---
    def get_id(self):
        return f"admin-{self.id}"

    # --- ALTERAÇÃO 3: PROPRIEDADE PARA IDENTIFICAR O ADMIN ---
    @property
    def is_admin(self):
        return True

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
# Modelo para os Colaboradores


class Colaborador(UserMixin, db.Model):  # --- ALTERAÇÃO 4: ADICIONA UserMixin ---
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

    # --- ALTERAÇÃO 5: MÉTODO get_id() PARA COLABORADOR ---
    def get_id(self):
        return f"colaborador-{self.id}"

    # --- ALTERAÇÃO 6: PROPRIEDADE PARA DIFERENCIAR DO ADMIN ---
    @property
    def is_admin(self):
        return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
# Modelo para os Avisos


class Aviso(db.Model):
    # GARANTA QUE ESTA LINHA ESTÁ EXATAMENTE ASSIM:
    id = db.Column(db.Integer, primary_key=True)

    # ... e que as outras colunas estão aqui embaixo
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(length=200), nullable=True)
    link_texto = db.Column(db.String(length=100), nullable=True)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        """Converte o objeto Aviso para um dicionário, incluindo data formatada."""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'conteudo': self.conteudo,
            'link_url': self.link_url,
            'link_texto': self.link_texto,

            'data_criacao_iso': self.data_criacao.isoformat() if self.data_criacao else None,

            'data_criacao_fmt': self.data_criacao.strftime('%d/%m') if self.data_criacao else None
        }


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


class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    # Cor padrão do FullCalendar
    color = db.Column(db.String(20), nullable=True, default='#3788d8')

    # Chave estrangeira para ligar o evento ao utilizador que o criou
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        """Converte o objeto Evento para um dicionário compatível com FullCalendar."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start': self.start.isoformat(),
            'end': self.end.isoformat() if self.end else None,
            'location': self.location,
            'color': self.color,
            'creator': User.query.get(self.user_id).username
        }

    def __repr__(self):
        return f'<Evento {self.title}>'
