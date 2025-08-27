from __future__ import annotations
from datetime import datetime
from app import db

# ADICIONE ESTA IMPORTAÇÃO PARA ACESSAR O MODELO COLABORADOR
from app.models import Colaborador


class NewsPost(db.Model):
    __tablename__ = 'tb_news_post'
    id = db.Column(db.Integer, primary_key=True)
    autor_id = db.Column(db.Integer, db.ForeignKey(
        'colaborador.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo_md = db.Column(db.Text, nullable=True)
    midias_json = db.Column(db.JSON, nullable=True)
    publicado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fixado_ordem = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum('rascunho', 'publicado',
                       name='news_post_status'), default='publicado')

    # ADICIONE A LINHA ABAIXO PARA CRIAR A RELAÇÃO 'autor'
    autor = db.relationship('Colaborador', backref='news_posts')

    comentarios = db.relationship('NewsComentario', backref='post', lazy=True)
    reacoes = db.relationship('NewsReacao', backref='post', lazy=True)
    avaliacoes = db.relationship('NewsAvaliacao', backref='post', lazy=True)


class NewsReacao(db.Model):
    __tablename__ = 'tb_news_reacao'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey(
        'tb_news_post.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey(
        'colaborador.id'), nullable=False)
    tipo = db.Column(db.Enum('like', 'palmas', 'coracao', 'genial',
                     'feliz', name='news_reacao_tipo'), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint(
        'post_id', 'usuario_id', name='uix_reacao_post_usuario'),)


class NewsComentario(db.Model):
    __tablename__ = 'tb_news_comentario'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey(
        'tb_news_post.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey(
        'colaborador.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    gif_id = db.Column(db.String(64), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    editado_em = db.Column(db.DateTime, nullable=True)
    excluido = db.Column(db.Boolean, default=False)

    # ADICIONE A LINHA ABAIXO PARA CRIAR A RELAÇÃO 'usuario'
    usuario = db.relationship('Colaborador', backref='news_comentarios')


class NewsAvaliacao(db.Model):
    __tablename__ = 'tb_news_avaliacao'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey(
        'tb_news_post.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey(
        'colaborador.id'), nullable=False)
    estrelas = db.Column(db.Integer, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint(
        'post_id', 'usuario_id', name='uix_avaliacao_post_usuario'),)


class NewsEnquete(db.Model):
    __tablename__ = 'tb_news_enquete'
    id = db.Column(db.Integer, primary_key=True)
    autor_id = db.Column(db.Integer, db.ForeignKey(
        'colaborador.id'), nullable=False)
    pergunta = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo_selecao = db.Column(
        db.Enum('single', 'multi', name='news_enquete_tipo'), default='single')
    anonima = db.Column(db.Boolean, default=True)
    vis_resultado = db.Column(db.Enum(
        'always', 'after_vote', 'after_close', name='news_enquete_vis'), default='after_vote')
    inicio_em = db.Column(db.DateTime, nullable=True)
    fim_em = db.Column(db.DateTime, nullable=True)
    fixado_ordem = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum('rascunho', 'aberta', 'encerrada',
                       name='news_enquete_status'), default='aberta')

    opcoes = db.relationship('NewsEnqueteOpcao', backref='enquete', lazy=True)


class NewsEnqueteOpcao(db.Model):
    __tablename__ = 'tb_news_enquete_opcao'
    id = db.Column(db.Integer, primary_key=True)
    enquete_id = db.Column(db.Integer, db.ForeignKey(
        'tb_news_enquete.id'), nullable=False)
    texto = db.Column(db.String(255), nullable=False)
    ordem = db.Column(db.Integer, nullable=False)


class NewsEnqueteVoto(db.Model):
    __tablename__ = 'tb_news_enquete_voto'
    id = db.Column(db.Integer, primary_key=True)
    enquete_id = db.Column(db.Integer, db.ForeignKey(
        'tb_news_enquete.id'), nullable=False)
    opcao_id = db.Column(db.Integer, db.ForeignKey(
        'tb_news_enquete_opcao.id'), nullable=False)
    usuario_id = db.Column(db.Integer, nullable=True)
    hash_anon = db.Column(db.String(64), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('enquete_id', 'usuario_id',
                            'opcao_id', name='uix_voto_ident'),
        db.UniqueConstraint('enquete_id', 'hash_anon',
                            'opcao_id', name='uix_voto_anon'),
    )
