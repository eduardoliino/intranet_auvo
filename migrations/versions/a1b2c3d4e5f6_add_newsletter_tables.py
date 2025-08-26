"""add newsletter tables

Revision ID: a1b2c3d4e5f6
Revises: e0061a47d8c5
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'e0061a47d8c5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('tb_news_post',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('autor_id', sa.Integer, sa.ForeignKey('colaborador.id'), nullable=False),
        sa.Column('titulo', sa.String(200), nullable=False),
        sa.Column('conteudo_md', sa.Text),
        sa.Column('midias_json', sa.JSON),
        sa.Column('publicado_em', sa.DateTime, nullable=False),
        sa.Column('atualizado_em', sa.DateTime, nullable=False),
        sa.Column('fixado_ordem', sa.Integer),
        sa.Column('status', sa.Enum('rascunho','publicado', name='news_post_status'), nullable=False, server_default='publicado')
    )
    op.create_table('tb_news_reacao',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('post_id', sa.Integer, sa.ForeignKey('tb_news_post.id'), nullable=False),
        sa.Column('usuario_id', sa.Integer, sa.ForeignKey('colaborador.id'), nullable=False),
        sa.Column('tipo', sa.Enum('like','palmas','coracao','genial','feliz', name='news_reacao_tipo'), nullable=False),
        sa.Column('criado_em', sa.DateTime, nullable=False),
        sa.UniqueConstraint('post_id','usuario_id', name='uix_reacao_post_usuario')
    )
    op.create_table('tb_news_comentario',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('post_id', sa.Integer, sa.ForeignKey('tb_news_post.id'), nullable=False),
        sa.Column('usuario_id', sa.Integer, sa.ForeignKey('colaborador.id'), nullable=False),
        sa.Column('texto', sa.Text, nullable=False),
        sa.Column('gif_id', sa.String(64)),
        sa.Column('criado_em', sa.DateTime, nullable=False),
        sa.Column('editado_em', sa.DateTime),
        sa.Column('excluido', sa.Boolean, nullable=False, server_default='0')
    )
    op.create_table('tb_news_avaliacao',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('post_id', sa.Integer, sa.ForeignKey('tb_news_post.id'), nullable=False),
        sa.Column('usuario_id', sa.Integer, sa.ForeignKey('colaborador.id'), nullable=False),
        sa.Column('estrelas', sa.Integer, nullable=False),
        sa.Column('criado_em', sa.DateTime, nullable=False),
        sa.UniqueConstraint('post_id','usuario_id', name='uix_avaliacao_post_usuario')
    )
    op.create_table('tb_news_enquete',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('autor_id', sa.Integer, sa.ForeignKey('colaborador.id'), nullable=False),
        sa.Column('pergunta', sa.Text, nullable=False),
        sa.Column('descricao', sa.Text),
        sa.Column('tipo_selecao', sa.Enum('single','multi', name='news_enquete_tipo'), server_default='single'),
        sa.Column('anonima', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('vis_resultado', sa.Enum('always','after_vote','after_close', name='news_enquete_vis'), server_default='after_vote'),
        sa.Column('inicio_em', sa.DateTime),
        sa.Column('fim_em', sa.DateTime),
        sa.Column('fixado_ordem', sa.Integer),
        sa.Column('status', sa.Enum('rascunho','aberta','encerrada', name='news_enquete_status'), server_default='aberta')
    )
    op.create_table('tb_news_enquete_opcao',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('enquete_id', sa.Integer, sa.ForeignKey('tb_news_enquete.id'), nullable=False),
        sa.Column('texto', sa.String(255), nullable=False),
        sa.Column('ordem', sa.Integer, nullable=False)
    )
    op.create_table('tb_news_enquete_voto',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('enquete_id', sa.Integer, sa.ForeignKey('tb_news_enquete.id'), nullable=False),
        sa.Column('opcao_id', sa.Integer, sa.ForeignKey('tb_news_enquete_opcao.id'), nullable=False),
        sa.Column('usuario_id', sa.Integer),
        sa.Column('hash_anon', sa.String(64)),
        sa.Column('criado_em', sa.DateTime, nullable=False),
        sa.UniqueConstraint('enquete_id','usuario_id','opcao_id', name='uix_voto_ident'),
        sa.UniqueConstraint('enquete_id','hash_anon','opcao_id', name='uix_voto_anon')
    )
    op.create_table('tb_gam_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('usuario_id', sa.Integer, nullable=False),
        sa.Column('acao', sa.String(50), nullable=False),
        sa.Column('ref_tipo', sa.String(20), nullable=False),
        sa.Column('ref_id', sa.Integer, nullable=False),
        sa.Column('meta_json', sa.JSON),
        sa.Column('criado_em', sa.DateTime, nullable=False)
    )


def downgrade():
    op.drop_table('tb_gam_log')
    op.drop_table('tb_news_enquete_voto')
    op.drop_table('tb_news_enquete_opcao')
    op.drop_table('tb_news_enquete')
    op.drop_table('tb_news_avaliacao')
    op.drop_table('tb_news_comentario')
    op.drop_table('tb_news_reacao')
    op.drop_table('tb_news_post')
    sa.Enum(name='news_post_status').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='news_reacao_tipo').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='news_enquete_tipo').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='news_enquete_vis').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='news_enquete_status').drop(op.get_bind(), checkfirst=False)
