from datetime import datetime
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Evento
from . import admin
from .utils import admin_required


@admin.route('/eventos')
@login_required
@admin_required
def gerenciar_eventos():
    eventos = Evento.query.order_by(Evento.start.desc()).all()
    eventos_json = [evento.to_dict() for evento in eventos]
    return render_template('admin/gerenciar_eventos.html', eventos=eventos_json)


@admin.route('/eventos/novo', methods=['POST'])
@login_required
@admin_required
def novo_evento():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('start'):
        return jsonify({'success': False, 'message': 'Título e data de início são obrigatórios.'}), 400
    novo_evento = Evento(
        title=data['title'],
        start=datetime.fromisoformat(data['start']),
        end=datetime.fromisoformat(data['end']) if data.get('end') else None,
        description=data.get('description'),
        location=data.get('location'),
        user_id=current_user.id,
    )
    db.session.add(novo_evento)
    db.session.commit()
    return jsonify({'success': True, 'evento': novo_evento.to_dict()})


@admin.route('/eventos/editar/<int:id>', methods=['POST'])
@login_required
@admin_required
def editar_evento(id):
    evento = Evento.query.get_or_404(id)
    data = request.get_json()
    if not data or not data.get('title') or not data.get('start'):
        return jsonify({'success': False, 'message': 'Título e data de início são obrigatórios.'}), 400
    evento.title = data['title']
    evento.start = datetime.fromisoformat(data['start'])
    evento.end = datetime.fromisoformat(data['end']) if data.get('end') else None
    evento.description = data.get('description')
    evento.location = data.get('location')
    db.session.commit()
    return jsonify({'success': True, 'evento': evento.to_dict()})


@admin.route('/eventos/remover/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def remover_evento(id):
    evento = Evento.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Evento removido com sucesso.'})
