from flask import render_template, request, jsonify
from flask_login import login_required
from app import db
from app.models import Ouvidoria
from . import admin
from .utils import admin_required


@admin.route('/ouvidoria')
@login_required
@admin_required
def gerenciar_ouvidoria():
    entradas_obj = Ouvidoria.query.order_by(Ouvidoria.data_envio.desc()).all()
    entradas_json = [
        {
            'id': e.id,
            'data_envio': e.data_envio.isoformat(),
            'tipo_denuncia': e.tipo_denuncia,
            'mensagem': e.mensagem,
            'anonima': e.anonima,
            'nome': e.nome,
            'contato': e.contato,
            'status': e.status,
        }
        for e in entradas_obj
    ]
    return render_template('admin/gerenciar_ouvidoria.html', entradas=entradas_json)


@admin.route('/ouvidoria/atualizar_status/<int:id>', methods=['POST'])
@login_required
@admin_required
def atualizar_status_ouvidoria(id):
    entrada = Ouvidoria.query.get_or_404(id)
    data = request.get_json()
    novo_status = data.get('status')
    if novo_status in ['Nova', 'Em análise', 'Resolvida']:
        entrada.status = novo_status
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Status inválido.'}), 400
