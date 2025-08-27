from __future__ import annotations
from datetime import datetime, timedelta
import hashlib
import json
import re
from collections import Counter

from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload, subqueryload

from app import db
from app.utils.gamificacao_utils import registrar_acao

from . import newsletter_bp
from .models import (
    NewsPost,
    NewsReacao,
    NewsComentario,
    NewsAvaliacao,
    NewsEnquete,
    NewsEnqueteOpcao,
    NewsEnqueteVoto,
)


# Helpers -------------------------------------------------

def sanitize_comment(text: str) -> str:
    if re.search(r"https?://", text):
        raise ValueError("Links não são permitidos nos comentários")
    return text


def get_user_hash(enquete_id: int, usuario_id: int) -> str:
    base = f"{enquete_id}:{usuario_id}:pepper".encode()
    return hashlib.sha256(base).hexdigest()


# Feed ----------------------------------------------------

@newsletter_bp.route('/newsletter')
@login_required
def feed():
    tipo = request.args.get('tipo', 'all')
    search = request.args.get('search', '')
    periodo = int(request.args.get('periodo', 30))
    limite = datetime.utcnow() - timedelta(days=periodo)

    posts_q = NewsPost.query.options(joinedload(NewsPost.autor)).filter(
        NewsPost.publicado_em >= limite, NewsPost.status == 'publicado')
    enquetes_q = NewsEnquete.query.filter(NewsEnquete.status != 'rascunho')

    if search:
        posts_q = posts_q.filter(NewsPost.titulo.ilike(f"%{search}%"))
        enquetes_q = enquetes_q.filter(
            NewsEnquete.pergunta.ilike(f"%{search}%"))

    fixados_posts = posts_q.filter(NewsPost.fixado_ordem.isnot(
        None)).order_by(NewsPost.fixado_ordem).all()
    fixados_enquetes = enquetes_q.filter(NewsEnquete.fixado_ordem.isnot(
        None)).order_by(NewsEnquete.fixado_ordem).all()

    feed_posts = []
    if tipo in ('all', 'post'):
        feed_posts.extend(posts_q.filter(NewsPost.fixado_ordem.is_(
            None)).order_by(NewsPost.publicado_em.desc()).all())
    feed_enquetes = []
    if tipo in ('all', 'enquete'):
        feed_enquetes.extend(enquetes_q.filter(NewsEnquete.fixado_ordem.is_(
            None)).order_by(NewsEnquete.inicio_em.desc()).all())

    return render_template(
        'newsletter.html',
        fixados_posts=fixados_posts,
        fixados_enquetes=fixados_enquetes,
        feed_posts=feed_posts,
        feed_enquetes=feed_enquetes,
    )


# Post modais ---------------------------------------------

@newsletter_bp.route('/newsletter/post/<int:post_id>')
@login_required
def ver_post(post_id: int):
    # Substitua a linha antiga por esta consulta otimizada
    post = NewsPost.query.options(
        subqueryload(NewsPost.comentarios).joinedload(NewsComentario.usuario),
        # Garante que as reações sejam carregadas
        subqueryload(NewsPost.reacoes)
    ).get_or_404(post_id)

    # Contabiliza as reações
    reaction_counts = Counter(r.tipo for r in post.reacoes)

    # Encontra a reação do usuário atual
    user_reaction = next(
        (r.tipo for r in post.reacoes if r.usuario_id == current_user.id), None)

    return render_template(
        'newsletter_post_modal.html',
        post=post,
        reaction_counts=reaction_counts,
        user_reaction=user_reaction
    )


@newsletter_bp.route('/newsletter/enquete/<int:enquete_id>')
@login_required
def ver_enquete(enquete_id: int):
    enquete = NewsEnquete.query.get_or_404(enquete_id)
    return render_template('newsletter_enquete_modal.html', enquete=enquete)


# Reações -------------------------------------------------

@newsletter_bp.post('/api/news/post/<int:post_id>/reacao')
@login_required
def reagir(post_id: int):
    tipo = request.form.get('tipo')
    if tipo not in {'like', 'palmas', 'coracao', 'genial', 'feliz', 'heart', 'lightbulb', 'surprise', 'rocket', 'grin', 'hearteyes'}:
        abort(400)

    reacao = NewsReacao.query.filter_by(
        post_id=post_id, usuario_id=current_user.id).first()
    if reacao:
        reacao.tipo = tipo
    else:
        reacao = NewsReacao(
            post_id=post_id, usuario_id=current_user.id, tipo=tipo)
        db.session.add(reacao)

    db.session.commit()
    registrar_acao(current_user.id, "reagir_post", "post", post_id)

    # Renderiza o template multi-swap
    return render_multi_swap(post_id)


@newsletter_bp.delete('/api/news/post/<int:post_id>/reacao')
@login_required
def remover_reacao(post_id: int):
    reacao = NewsReacao.query.filter_by(
        post_id=post_id, usuario_id=current_user.id).first()
    if reacao:
        db.session.delete(reacao)
        db.session.commit()
        registrar_acao(current_user.id, "remover_reacao", "post", post_id)

    # Renderiza o template multi-swap
    return render_multi_swap(post_id)


# Adicione esta função helper para evitar repetição de código
def render_multi_swap(post_id):
    post = NewsPost.query.options(
        subqueryload(NewsPost.reacoes),
        subqueryload(NewsPost.comentarios)
    ).get_or_404(post_id)

    reaction_counts = Counter(r.tipo for r in post.reacoes)
    user_reaction = next(
        (r.tipo for r in post.reacoes if r.usuario_id == current_user.id), None)

    # Dicionário com os dados completos das reações
    reaction_types = {
        'heart': {'icon': 'bi-heart-fill', 'name': 'Coração'},
        'lightbulb': {'icon': 'bi-lightbulb-fill', 'name': 'Genial'},
        'rocket': {'icon': 'bi-rocket-takeoff-fill', 'name': 'Foguete'},
        'grin': {'icon': 'bi-emoji-grin-fill', 'name': 'Feliz'},
        'hearteyes': {'icon': 'bi-emoji-heart-eyes-fill', 'name': 'Amei'},
        'surprise': {'icon': 'bi-emoji-surprise-fill', 'name': 'Uau'},
    }

    # Ordena as reações: as mais contadas primeiro
    sorted_reactions = sorted(
        reaction_types.items(),
        key=lambda item: reaction_counts.get(item[0], 0),
        reverse=True
    )

    return render_template(
        'partials/_multi_swap_reactions.html',
        post=post,
        reaction_counts=reaction_counts,
        user_reaction=user_reaction,
        sorted_reactions=sorted_reactions  # Envia a lista ordenada para o template
    )

# Comentários --------------------------------------------


@newsletter_bp.get('/api/news/post/<int:post_id>/comentarios')
@login_required
def listar_comentarios(post_id: int):
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    comentarios = NewsComentario.query.filter_by(post_id=post_id, excluido=False) \
        .order_by(NewsComentario.criado_em).paginate(page=page, per_page=limit, error_out=False)
    data = [
        {
            'id': c.id,
            'usuario_id': c.usuario_id,
            'texto': c.texto,
            'gif_id': c.gif_id,
            'criado_em': c.criado_em.isoformat(),
        } for c in comentarios.items
    ]
    return jsonify({'comentarios': data, 'total': comentarios.total})


@newsletter_bp.post('/api/news/post/<int:post_id>/comentarios')
@login_required
def criar_comentario(post_id: int):
    texto = request.json.get('texto', '').strip()
    gif_id = request.json.get('gif_id')
    try:
        texto = sanitize_comment(texto)
    except ValueError as e:
        abort(400, str(e))
    comentario = NewsComentario(
        post_id=post_id, usuario_id=current_user.id, texto=texto, gif_id=gif_id)
    db.session.add(comentario)
    db.session.commit()
    registrar_acao(current_user.id, "comentar_post", "post", post_id)
    return jsonify({'id': comentario.id})


@newsletter_bp.patch('/api/news/comentario/<int:comentario_id>')
@login_required
def editar_comentario(comentario_id: int):
    comentario = NewsComentario.query.get_or_404(comentario_id)
    if comentario.usuario_id != current_user.id and not current_user.is_admin:
        abort(403)
    texto = request.json.get('texto', '').strip()
    try:
        comentario.texto = sanitize_comment(texto)
        comentario.editado_em = datetime.utcnow()
        db.session.commit()
        registrar_acao(current_user.id, "editar_comentario",
                       "post", comentario_id)
    except ValueError as e:
        abort(400, str(e))
    return jsonify({'status': 'ok'})


@newsletter_bp.delete('/api/news/comentario/<int:comentario_id>')
@login_required
def excluir_comentario(comentario_id: int):
    comentario = NewsComentario.query.get_or_404(comentario_id)
    if comentario.usuario_id != current_user.id and not current_user.is_admin:
        abort(403)
    comentario.excluido = True
    db.session.commit()
    registrar_acao(current_user.id, "excluir_comentario",
                   "post", comentario_id)
    return jsonify({'status': 'ok'})


# Avaliação ----------------------------------------------

@newsletter_bp.put('/api/news/post/<int:post_id>/avaliacao')
@login_required
def avaliar_post(post_id: int):
    estrelas = int(request.json.get('estrelas', 0))
    if not 1 <= estrelas <= 5:
        abort(400)
    avaliacao = NewsAvaliacao.query.filter_by(
        post_id=post_id, usuario_id=current_user.id).first()
    if avaliacao:
        avaliacao.estrelas = estrelas
    else:
        avaliacao = NewsAvaliacao(
            post_id=post_id, usuario_id=current_user.id, estrelas=estrelas)
        db.session.add(avaliacao)
    db.session.commit()
    registrar_acao(current_user.id, "avaliar_post",
                   "post", post_id, {"estrelas": estrelas})
    return jsonify({'status': 'ok'})


# Enquetes ------------------------------------------------

@newsletter_bp.post('/api/news/enquete/<int:enquete_id>/voto')
@login_required
def votar_enquete(enquete_id: int):
    enquete = NewsEnquete.query.get_or_404(enquete_id)
    if enquete.status != 'aberta':
        abort(400, 'Enquete não está aberta')
    opcoes = request.json.get('opcoes', [])
    if enquete.tipo_selecao == 'single' and len(opcoes) != 1:
        abort(400)
    if enquete.tipo_selecao == 'multi' and len(opcoes) < 1:
        abort(400)

    usuario_id = current_user.id if not enquete.anonima else None
    hash_anon = None
    if enquete.anonima:
        hash_anon = get_user_hash(enquete.id, current_user.id)

    # remove votos anteriores
    if enquete.anonima:
        NewsEnqueteVoto.query.filter_by(
            enquete_id=enquete.id, hash_anon=hash_anon).delete()
    else:
        NewsEnqueteVoto.query.filter_by(
            enquete_id=enquete.id, usuario_id=current_user.id).delete()

    for opcao_id in opcoes:
        voto = NewsEnqueteVoto(
            enquete_id=enquete.id,
            opcao_id=opcao_id,
            usuario_id=usuario_id,
            hash_anon=hash_anon,
        )
        db.session.add(voto)
    db.session.commit()
    registrar_acao(current_user.id, "votar_enquete",
                   "enquete", enquete_id, {"opcoes": opcoes})
    return jsonify({'status': 'ok'})


@newsletter_bp.get('/api/news/enquete/<int:enquete_id>/resultado')
@login_required
def resultado_enquete(enquete_id: int):
    enquete = NewsEnquete.query.get_or_404(enquete_id)
    pode_ver = False
    if enquete.vis_resultado == 'always':
        pode_ver = True
    elif enquete.vis_resultado == 'after_vote':
        if enquete.anonima:
            hash_anon = get_user_hash(enquete.id, current_user.id)
            voto = NewsEnqueteVoto.query.filter_by(
                enquete_id=enquete.id, hash_anon=hash_anon).first()
        else:
            voto = NewsEnqueteVoto.query.filter_by(
                enquete_id=enquete.id, usuario_id=current_user.id).first()
        if voto:
            pode_ver = True
    elif enquete.vis_resultado == 'after_close' and enquete.status == 'encerrada':
        pode_ver = True
    if not pode_ver:
        abort(403)
    resultados = (
        db.session.query(NewsEnqueteOpcao.id, NewsEnqueteOpcao.texto,
                         db.func.count(NewsEnqueteVoto.id))
        .outerjoin(NewsEnqueteVoto, NewsEnqueteVoto.opcao_id == NewsEnqueteOpcao.id)
        .filter(NewsEnqueteOpcao.enquete_id == enquete.id)
        .group_by(NewsEnqueteOpcao.id)
        .order_by(NewsEnqueteOpcao.ordem)
        .all()
    )
    data = [{'id': oid, 'texto': texto, 'votos': votos}
            for oid, texto, votos in resultados]
    return jsonify({'opcoes': data})


# Admin ---------------------------------------------------

@newsletter_bp.route('/newsletter/admin')
@login_required
def admin_page():
    if not current_user.is_admin:
        abort(403)
    posts = NewsPost.query.order_by(NewsPost.publicado_em.desc()).all()
    enquetes = NewsEnquete.query.order_by(NewsEnquete.id.desc()).all()
    return render_template('admin/gerenciar_newsletter.html', posts=posts, enquetes=enquetes)


@newsletter_bp.post('/api/news/post')
@login_required
def criar_post():
    if not current_user.is_admin:
        abort(403)
    data = request.json
    post = NewsPost(
        autor_id=current_user.id,
        titulo=data.get('titulo'),
        conteudo_md=data.get('conteudo_md'),
        midias_json=data.get('midias_json'),
        publicado_em=datetime.utcnow(),
        status=data.get('status', 'publicado'),
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'id': post.id})


@newsletter_bp.patch('/api/news/post/<int:post_id>')
@login_required
def editar_post(post_id: int):
    if not current_user.is_admin:
        abort(403)
    post = NewsPost.query.get_or_404(post_id)
    data = request.json
    for campo in ['titulo', 'conteudo_md', 'midias_json', 'status']:
        if campo in data:
            setattr(post, campo, data[campo])
    db.session.commit()
    return jsonify({'status': 'ok'})


@newsletter_bp.delete('/api/news/post/<int:post_id>')
@login_required
def excluir_post(post_id: int):
    if not current_user.is_admin:
        abort(403)
    post = NewsPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'status': 'ok'})


@newsletter_bp.post('/api/news/enquete')
@login_required
def criar_enquete():
    if not current_user.is_admin:
        abort(403)
    data = request.json
    enquete = NewsEnquete(
        autor_id=current_user.id,
        pergunta=data['pergunta'],
        descricao=data.get('descricao'),
        tipo_selecao=data.get('tipo_selecao', 'single'),
        anonima=data.get('anonima', True),
        vis_resultado=data.get('vis_resultado', 'after_vote'),
        inicio_em=data.get('inicio_em'),
        fim_em=data.get('fim_em'),
    )
    db.session.add(enquete)
    db.session.flush()
    opcoes = data.get('opcoes', [])
    for idx, texto in enumerate(opcoes):
        db.session.add(NewsEnqueteOpcao(
            enquete_id=enquete.id, texto=texto, ordem=idx))
    db.session.commit()
    return jsonify({'id': enquete.id})


@newsletter_bp.patch('/api/news/enquete/<int:enquete_id>')
@login_required
def editar_enquete(enquete_id: int):
    if not current_user.is_admin:
        abort(403)
    enquete = NewsEnquete.query.get_or_404(enquete_id)
    data = request.json
    for campo in ['pergunta', 'descricao', 'tipo_selecao', 'anonima', 'vis_resultado', 'inicio_em', 'fim_em', 'status']:
        if campo in data:
            setattr(enquete, campo, data[campo])
    db.session.commit()
    return jsonify({'status': 'ok'})


@newsletter_bp.post('/api/news/enquete/<int:enquete_id>/encerrar')
@login_required
def encerrar_enquete(enquete_id: int):
    if not current_user.is_admin:
        abort(403)
    enquete = NewsEnquete.query.get_or_404(enquete_id)
    enquete.status = 'encerrada'
    db.session.commit()
    return jsonify({'status': 'ok'})


@newsletter_bp.post('/api/news/fixar')
@login_required
def fixar():
    if not current_user.is_admin:
        abort(403)
    tipo = request.json.get('tipo')
    ref_id = request.json.get('ref_id')
    ordem = request.json.get('ordem')
    if tipo == 'post':
        obj = NewsPost.query.get_or_404(ref_id)
    else:
        obj = NewsEnquete.query.get_or_404(ref_id)
    obj.fixado_ordem = ordem
    db.session.commit()
    return jsonify({'status': 'ok'})


@newsletter_bp.delete('/api/news/fixar/<string:tipo>/<int:ref_id>')
@login_required
def desfazer_fixacao(tipo: str, ref_id: int):
    if not current_user.is_admin:
        abort(403)
    if tipo == 'post':
        obj = NewsPost.query.get_or_404(ref_id)
    else:
        obj = NewsEnquete.query.get_or_404(ref_id)
    obj.fixado_ordem = None
    db.session.commit()
    return jsonify({'status': 'ok'})


@newsletter_bp.route('/newsletter/post/<int:post_id>/_reactions')
@login_required
def render_post_reactions(post_id: int):
    """Renderiza apenas a seção de reações do post."""
    post = NewsPost.query.options(subqueryload(
        NewsPost.reacoes)).get_or_404(post_id)

    reaction_counts = Counter(r.tipo for r in post.reacoes)
    user_reaction = next(
        (r.tipo for r in post.reacoes if r.usuario_id == current_user.id), None)

    return render_template(
        'partials/_news_post_reactions.html',
        post=post,
        reaction_counts=reaction_counts,
        user_reaction=user_reaction
    )


@newsletter_bp.route('/newsletter/post/<int:post_id>/_footer')
@login_required
def render_post_footer(post_id: int):
    """Renderiza apenas o rodapé do card do post (contadores)."""
    post = NewsPost.query.get_or_404(post_id)
    return render_template('partials/_news_post_footer.html', post=post)


@newsletter_bp.route('/newsletter/post/<int:post_id>/_comments')
@login_required
def render_post_comments(post_id: int):
    """Renderiza apenas a lista de comentários do post."""
    post = NewsPost.query.options(
        subqueryload(NewsPost.comentarios).joinedload(NewsComentario.usuario)
    ).get_or_404(post_id)
    return render_template('partials/_news_post_comments.html', post=post)
