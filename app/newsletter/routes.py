from __future__ import annotations
from datetime import datetime, timedelta
from collections import Counter
from flask import render_template, request, jsonify, abort, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload, subqueryload

from app import db, socketio
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
from .utils import generate_embed_data, extract_source_url


@newsletter_bp.route('/newsletter')
@login_required
def feed():
    posts_q = NewsPost.query.options(joinedload(NewsPost.autor)).filter(
        NewsPost.status == 'publicado')

    all_posts = posts_q.order_by(
        NewsPost.fixado_ordem, NewsPost.publicado_em.desc()).all()
    for post in all_posts:
        post.source_url = extract_source_url(post.conteudo_md)

    fixados_posts = [p for p in all_posts if p.fixado_ordem is not None]
    feed_posts = [p for p in all_posts if p.fixado_ordem is None]

    enquetes_q = NewsEnquete.query.filter(NewsEnquete.status != 'rascunho').order_by(
        NewsEnquete.fixado_ordem, NewsEnquete.id.desc())
    all_enquetes = enquetes_q.all()
    fixados_enquetes = [e for e in all_enquetes if e.fixado_ordem is not None]
    feed_enquetes = [e for e in all_enquetes if e.fixado_ordem is None]

    return render_template(
        'newsletter.html',
        fixados_posts=fixados_posts,
        feed_posts=feed_posts,
        fixados_enquetes=fixados_enquetes,
        feed_enquetes=feed_enquetes,
    )


@newsletter_bp.route('/api/news/post_details')
@login_required
def get_post_details():
    post_id = request.args.get('post_id', type=int)
    # A linha abaixo que pegava a 'url' não é mais necessária e foi removida.

    if not post_id:
        return jsonify({'success': False, 'error': 'Post ID não fornecido'}), 400

    post = NewsPost.query.options(
        subqueryload(NewsPost.comentarios).joinedload(NewsComentario.usuario),
        subqueryload(NewsPost.reacoes)
    ).get_or_404(post_id)

    # A lógica de 'generate_embed_data' foi removida daqui.

    reaction_counts = Counter(r.tipo for r in post.reacoes)
    user_reaction = next(
        (r.tipo for r in post.reacoes if r.usuario_id == current_user.id), None)

    comments_data = [{
        'id': c.id,
        'user_id': c.usuario_id,
        'text': c.texto,
        'user_name': f"{c.usuario.nome} {c.usuario.sobrenome}",
        'user_initials': f"{c.usuario.nome[0] if c.usuario.nome else ''}{c.usuario.sobrenome[0] if c.usuario.sobrenome else ''}",
        'user_photo': url_for('static', filename=f'fotos_colaboradores/{c.usuario.foto_filename}') if c.usuario.foto_filename else None,
        'post_id': c.post_id
    } for c in sorted(post.comentarios, key=lambda c: c.criado_em) if not c.excluido]

    return jsonify({
        'success': True,
        'postId': post.id,
        'postTitle': post.titulo,
        # <-- CORREÇÃO: Enviando o conteúdo HTML completo do post.
        'post_html': post.conteudo_md,
        'reactions': {'counts': dict(reaction_counts), 'user_reaction': user_reaction},
        'comments': comments_data,
        'current_user': {
            'id': current_user.id,
            'is_admin': current_user.is_admin
        }
    })

# --- ROTA RESTAURADA ---


@newsletter_bp.route('/enquete/<int:enquete_id>')
@login_required
def ver_enquete(enquete_id: int):
    enquete = NewsEnquete.query.get_or_404(enquete_id)
    # Esta rota pode simplesmente renderizar um fragmento de HTML ou retornar JSON
    # Por simplicidade, vamos mantê-la retornando o template do modal de enquete
    return render_template('newsletter_enquete_modal.html', enquete=enquete)


@newsletter_bp.post('/api/news/post/<int:post_id>/reacao')
@login_required
def reagir(post_id: int):
    tipo = request.json.get('tipo')
    if not tipo:
        abort(400)

    reacao = NewsReacao.query.filter_by(
        post_id=post_id, usuario_id=current_user.id).first()
    action = ''
    if reacao:
        if reacao.tipo == tipo:
            db.session.delete(reacao)
            action = 'removed'
        else:
            reacao.tipo = tipo
            action = 'updated'
    else:
        reacao = NewsReacao(
            post_id=post_id, usuario_id=current_user.id, tipo=tipo)
        db.session.add(reacao)
        action = 'added'

    db.session.commit()

    post_reactions = NewsReacao.query.filter_by(post_id=post_id).all()
    reaction_counts = Counter(r.tipo for r in post_reactions)
    socketio.emit('update_reactions', {
                  'post_id': post_id, 'counts': dict(reaction_counts)})

    return jsonify({'success': True, 'action': action})


@newsletter_bp.post('/api/news/post/<int:post_id>/comentarios')
@login_required
def criar_comentario(post_id: int):
    texto = request.json.get('texto', '').strip()
    if not texto:
        return jsonify({'success': False, 'error': 'O comentário não pode estar vazio.'}), 400

    comentario = NewsComentario(
        post_id=post_id, usuario_id=current_user.id, texto=texto)
    db.session.add(comentario)
    db.session.commit()

    comment_data = {
        'id': comentario.id,
        'user_id': current_user.id,
        'post_id': post_id,
        'text': comentario.texto,
        'user_name': f"{current_user.nome} {current_user.sobrenome}",
        'user_initials': f"{(current_user.nome or ' ')[0]}{(current_user.sobrenome or ' ')[0]}",
        'user_photo': url_for('static', filename=f'fotos_colaboradores/{current_user.foto_filename}') if current_user.foto_filename else None
    }
    # Agora o evento 'new_comment' leva o post_id junto com os dados do comentário
    socketio.emit('new_comment', {'comment': comment_data})

    return jsonify({'success': True, 'comment': comment_data})

# --- Rotas de Admin ---


@newsletter_bp.route('/admin')
@login_required
def admin_page():
    if not current_user.is_admin:
        abort(403)
    # Paginação: 15 por página
    page = request.args.get('page', 1, type=int)
    pagination = NewsPost.query.order_by(NewsPost.publicado_em.desc()).paginate(
        page=page, per_page=15, error_out=False)
    # Render parcial para SPA-like updates
    if request.args.get('_partial') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            'admin/_newsletter_posts_list.html',
            posts=pagination.items,
            pagination=pagination,
        )
    # Render page completa
    return render_template(
        'admin/gerenciar_newsletter.html',
        posts=pagination.items,
        pagination=pagination,
    )


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
        publicado_em=datetime.utcnow(),
        status='publicado',
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
    for campo in ['titulo', 'conteudo_md', 'status']:
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
    # Remoção defensiva dos dependentes para evitar violação de NOT NULL
    NewsComentario.query.filter_by(
        post_id=post_id).delete(synchronize_session=False)
    NewsReacao.query.filter_by(post_id=post_id).delete(
        synchronize_session=False)
    NewsAvaliacao.query.filter_by(
        post_id=post_id).delete(synchronize_session=False)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'status': 'ok'})


@newsletter_bp.route('/api/news/feed')
@login_required
def api_feed():
    """
    Endpoint da API para buscar o feed da newsletter com paginação e pesquisa.
    """
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '', type=str)

    # Query base para posts e enquetes publicados
    posts_q = NewsPost.query.options(
        joinedload(NewsPost.autor),
        subqueryload(NewsPost.reacoes),
        subqueryload(NewsPost.comentarios)
    ).filter(NewsPost.status == 'publicado')

    enquetes_q = NewsEnquete.query.options(
        joinedload(NewsEnquete.opcoes)
    ).filter(NewsEnquete.status != 'rascunho')

    # Aplica o filtro de pesquisa se houver um termo
    if search_term:
        search_filter = f"%{search_term}%"
        posts_q = posts_q.filter(NewsPost.titulo.ilike(search_filter))
        enquetes_q = enquetes_q.filter(
            NewsEnquete.pergunta.ilike(search_filter))

    # Combina e ordena os resultados
    # Esta é uma forma simplificada de combinar. Para grandes volumes, uma abordagem mais complexa seria necessária.
    all_items = sorted(
        posts_q.all() + enquetes_q.all(),
        key=lambda x: getattr(x, 'publicado_em', getattr(
            x, 'inicio_em', datetime.min)) or datetime.min,
        reverse=True
    )

    # Paginação manual da lista combinada
    per_page = 12
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = all_items[start:end]
    has_next = len(all_items) > end

    feed_data = []
    for item in paginated_items:
        if isinstance(item, NewsPost):
            feed_data.append({
                'type': 'post',
                'id': item.id,
                'titulo': item.titulo,
                'conteudo_resumo': item.conteudo_md,  # Pode ser truncado se necessário
                'autor_nome': f"{item.autor.nome} {item.autor.sobrenome}",
                'autor_foto': url_for('static', filename=f'fotos_colaboradores/{item.autor.foto_filename}') if item.autor.foto_filename else None,
                'autor_iniciais': f"{(item.autor.nome or ' ')[0]}{(item.autor.sobrenome or ' ')[0]}",
                'publicado_em': item.publicado_em.strftime('%d de %B de %Y'),
                'total_reacoes': len(item.reacoes),
                'total_comentarios': len([c for c in item.comentarios if not c.excluido])
            })
        elif isinstance(item, NewsEnquete):
            feed_data.append({
                'type': 'enquete',
                'id': item.id,
                'pergunta': item.pergunta,
                'status': 'Encerrada' if item.status == 'encerrada' else 'Aberta',
                'opcoes': [{'texto': o.texto} for o in sorted(item.opcoes, key=lambda opt: opt.ordem)]
            })

    return jsonify({
        'feed': feed_data,
        'has_next': has_next
    })


@newsletter_bp.delete('/api/news/comment/<int:comment_id>')
@login_required
def excluir_comentario(comment_id: int):
    comentario = NewsComentario.query.get_or_404(comment_id)
    if not (current_user.id == comentario.usuario_id or current_user.is_admin):
        abort(403)  # Forbidden

    comentario.excluido = True
    db.session.commit()

    # Emite um evento via Socket.IO para notificar todos os clientes conectados
    socketio.emit('comment_deleted', {
                  'comment_id': comment_id, 'post_id': comentario.post_id})

    return jsonify({'success': True})