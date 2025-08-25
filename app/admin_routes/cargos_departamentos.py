from flask import render_template, request, flash, redirect, url_for, jsonify
from app import db
from app.models import ConfigLink, Colaborador, Cargo, Departamento
from . import admin
from .utils import permission_required


@admin.route('/cargos-departamentos', methods=['GET'])
@permission_required('gerenciar_cargos_departamentos')
def gerenciar_cargos_departamentos():
    """Painel de gestão de cargos, departamentos e configuração do CEO."""
    cargos_obj = Cargo.query.order_by(Cargo.titulo).all()
    cargos_json = [{'id': c.id, 'titulo': c.titulo} for c in cargos_obj]

    departamentos_obj = Departamento.query.order_by(Departamento.nome).all()
    departamentos_json = [{'id': d.id, 'nome': d.nome} for d in departamentos_obj]

    colaboradores = Colaborador.query.order_by(Colaborador.nome).all()
    config_ceo = ConfigLink.query.filter_by(chave='ceo_colaborador_id').first()
    ceo_id = int(config_ceo.valor) if config_ceo and config_ceo.valor else None

    return render_template(
        'admin/gerenciar_cargos_departamentos.html',
        cargos=cargos_json,
        departamentos=departamentos_json,
        colaboradores=colaboradores,
        ceo_id=ceo_id,
    )


@admin.route('/cargos-departamentos/ceo', methods=['POST'])
@permission_required('gerenciar_cargos_departamentos')
def definir_ceo():
    """Define qual colaborador será exibido como CEO no organograma."""
    ceo_id = request.form.get('ceo_id')
    config_ceo = ConfigLink.query.filter_by(chave='ceo_colaborador_id').first()
    if not config_ceo:
        config_ceo = ConfigLink(chave='ceo_colaborador_id')
        db.session.add(config_ceo)
    config_ceo.valor = ceo_id
    db.session.commit()
    flash('CEO do organograma definido com sucesso!', 'success')
    return redirect(url_for('admin.gerenciar_cargos_departamentos'))


@admin.route('/cargos/adicionar', methods=['POST'])
@permission_required('gerenciar_cargos_departamentos')
def adicionar_cargo():
    data = request.json
    titulo = data.get('titulo')
    if not titulo:
        return jsonify({'success': False, 'message': 'Título é obrigatório.'}), 400
    if Cargo.query.filter_by(titulo=titulo).first():
        return jsonify({'success': False, 'message': 'Este cargo já existe.'}), 400
    novo_cargo = Cargo(titulo=titulo)
    db.session.add(novo_cargo)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Cargo adicionado!', 'cargo': {'id': novo_cargo.id, 'titulo': novo_cargo.titulo}})


@admin.route('/cargos/editar/<int:id>', methods=['POST'])
@permission_required('gerenciar_cargos_departamentos')
def editar_cargo(id):
    cargo = Cargo.query.get_or_404(id)
    data = request.json
    novo_titulo = data.get('titulo')
    if not novo_titulo:
        return jsonify({'success': False, 'message': 'Título é obrigatório.'}), 400
    if novo_titulo != cargo.titulo and Cargo.query.filter_by(titulo=novo_titulo).first():
        return jsonify({'success': False, 'message': 'Este título de cargo já está em uso.'}), 400
    cargo.titulo = novo_titulo
    db.session.commit()
    return jsonify({'success': True, 'message': 'Cargo atualizado!', 'cargo': {'id': cargo.id, 'titulo': cargo.titulo}})


@admin.route('/cargos/remover/<int:id>', methods=['POST'])
@permission_required('gerenciar_cargos_departamentos')
def remover_cargo(id):
    cargo = Cargo.query.get_or_404(id)
    Colaborador.query.filter_by(cargo_id=id).update({'cargo_id': None})
    db.session.delete(cargo)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Cargo removido com sucesso!'})


@admin.route('/departamentos/adicionar', methods=['POST'])
@permission_required('gerenciar_cargos_departamentos')
def adicionar_departamento():
    data = request.json
    nome = data.get('nome')
    if not nome:
        return jsonify({'success': False, 'message': 'Nome é obrigatório.'}), 400
    if Departamento.query.filter_by(nome=nome).first():
        return jsonify({'success': False, 'message': 'Este departamento já existe.'}), 400
    novo_depto = Departamento(nome=nome)
    db.session.add(novo_depto)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Departamento adicionado!', 'departamento': {'id': novo_depto.id, 'nome': novo_depto.nome}})


@admin.route('/departamentos/editar/<int:id>', methods=['POST'])
@permission_required('gerenciar_cargos_departamentos')
def editar_departamento(id):
    depto = Departamento.query.get_or_404(id)
    data = request.json
    novo_nome = data.get('nome')
    if not novo_nome:
        return jsonify({'success': False, 'message': 'Nome é obrigatório.'}), 400
    if novo_nome != depto.nome and Departamento.query.filter_by(nome=novo_nome).first():
        return jsonify({'success': False, 'message': 'Este nome de departamento já está em uso.'}), 400
    depto.nome = novo_nome
    db.session.commit()
    return jsonify({'success': True, 'message': 'Departamento atualizado!', 'departamento': {'id': depto.id, 'nome': depto.nome}})


@admin.route('/departamentos/remover/<int:id>', methods=['POST'])
@permission_required('gerenciar_cargos_departamentos')
def remover_departamento(id):
    depto = Departamento.query.get_or_404(id)
    Colaborador.query.filter_by(departamento_id=id).update({'departamento_id': None})
    db.session.delete(depto)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Departamento removido com sucesso!'})
