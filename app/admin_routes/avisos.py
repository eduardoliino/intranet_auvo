from flask import render_template, request, jsonify
from flask_login import login_required
from app import db
from app.models import Aviso
from . import admin
from .utils import admin_required


@admin.route('/avisos')
@login_required
@admin_required
def gerenciar_avisos():
    """Exibe e permite a gestão dos avisos publicados."""
    avisos_objetos = Aviso.query.order_by(Aviso.id.desc()).all()
    avisos_json = [
        {
            'id': aviso.id,
            'titulo': aviso.titulo,
            'conteudo': aviso.conteudo,
            'link_url': aviso.link_url,
            'link_texto': aviso.link_texto,
        }
        for aviso in avisos_objetos
    ]
    return render_template('admin/gerenciar_avisos.html', avisos=avisos_json)


@admin.route('/avisos/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_aviso():
    """Regista um novo aviso no sistema."""
    titulo = request.form.get('titulo')
    conteudo = request.form.get('conteudo')
    link_url = request.form.get('link_url')
    link_texto = request.form.get('link_texto')
    if not titulo or not conteudo:
        return jsonify({'success': False, 'message': 'Título e conteúdo são obrigatórios.'}), 400
    novo_aviso = Aviso(
        titulo=titulo,
        conteudo=conteudo,
        link_url=link_url,
        link_texto=link_texto,
    )
    db.session.add(novo_aviso)
    db.session.commit()
    return jsonify({'success': True, 'aviso': {
        'id': novo_aviso.id,
        'titulo': novo_aviso.titulo,
        'conteudo': novo_aviso.conteudo,
        'link_url': novo_aviso.link_url,
        'link_texto': novo_aviso.link_texto
    }})


@admin.route('/avisos/remover/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def remover_aviso(id):
    """Exclui um aviso existente."""
    aviso = Aviso.query.get_or_404(id)
    db.session.delete(aviso)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Aviso removido com sucesso.'})
