import os
from datetime import datetime
from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required
from sqlalchemy.orm import joinedload
from app import db
from app.models import Destaque, Colaborador, Departamento
from . import admin
from .utils import admin_required, salvar_foto


@admin.route('/destaques')
@login_required
@admin_required
def gerenciar_destaques():
    destaques_obj = Destaque.query.options(
        joinedload(Destaque.colaborador).joinedload(Colaborador.departamento)
    ).order_by(Destaque.ano.desc(), Destaque.mes.desc()).all()

    colaboradores_obj = Colaborador.query.order_by(Colaborador.nome).all()
    departamentos_obj = Departamento.query.order_by(Departamento.nome).all()

    destaques_json = []
    for d in destaques_obj:
        destaques_json.append({
            'id': d.id,
            'titulo': d.titulo,
            'descricao': d.descricao,
            'mes': d.mes,
            'ano': d.ano,
            'imagem_filename': d.imagem_filename,
            'colaborador_id': d.colaborador_id,
            'colaborador_nome': f"{d.colaborador.nome} {d.colaborador.sobrenome}",
            'colaborador_foto': d.colaborador.foto_filename,
            'departamento_id': d.colaborador.departamento_id,
        })

    colaboradores_json = [
        {'id': c.id, 'nome': f"{c.nome} {c.sobrenome}"} for c in colaboradores_obj
    ]

    anos_disponiveis = sorted(list(set(d.ano for d in destaques_obj)), reverse=True)
    current_year = datetime.utcnow().year
    form_anos = list(range(2024, current_year + 3))

    return render_template(
        'admin/gerenciar_destaques.html',
        destaques=destaques_json,
        colaboradores=colaboradores_json,
        departamentos=departamentos_obj,
        anos=anos_disponiveis,
        form_anos=form_anos,
    )


@admin.route('/destaques/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_destaque():
    titulo = request.form.get('titulo')
    colaborador_id = request.form.get('colaborador_id')
    descricao = request.form.get('descricao')
    mes = request.form.get('mes')
    ano = request.form.get('ano')

    if not all([titulo, colaborador_id, mes, ano]):
        return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios.'}), 400

    imagem_filename = None
    if 'imagem_destaque' in request.files:
        imagem_enviada = request.files['imagem_destaque']
        if imagem_enviada.filename != '':
            imagem_filename = salvar_foto(imagem_enviada)

    novo_destaque = Destaque(
        titulo=titulo,
        colaborador_id=int(colaborador_id),
        descricao=descricao,
        mes=int(mes),
        ano=int(ano),
        imagem_filename=imagem_filename,
    )
    db.session.add(novo_destaque)
    db.session.commit()

    destaque_json = {
        'id': novo_destaque.id,
        'titulo': novo_destaque.titulo,
        'descricao': novo_destaque.descricao,
        'mes': novo_destaque.mes,
        'ano': novo_destaque.ano,
        'imagem_filename': novo_destaque.imagem_filename,
        'colaborador_id': novo_destaque.colaborador_id,
        'colaborador_nome': f"{novo_destaque.colaborador.nome} {novo_destaque.colaborador.sobrenome}",
        'colaborador_foto': novo_destaque.colaborador.foto_filename,
        'departamento_id': novo_destaque.colaborador.departamento_id,
    }
    return jsonify({'success': True, 'destaque': destaque_json})


@admin.route('/destaques/remover/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def remover_destaque(id):
    destaque = Destaque.query.get_or_404(id)
    if destaque.imagem_filename:
        caminho_imagem = os.path.join(
            current_app.root_path, 'static/fotos_colaboradores', destaque.imagem_filename
        )
        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)
    db.session.delete(destaque)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Destaque removido com sucesso.'})


@admin.route('/destaques/remover-em-massa', methods=['POST'])
@admin_required
def remover_destaques_em_massa():
    data = request.get_json()
    mes = data.get('mes')
    ano = data.get('ano')

    if not mes or not ano:
        return jsonify({'success': False, 'message': 'Mês e ano são obrigatórios.'}), 400

    destaques_para_remover = Destaque.query.filter_by(mes=mes, ano=ano).all()

    if not destaques_para_remover:
        return jsonify({'success': False, 'message': 'Nenhum destaque encontrado para este período.'}), 404

    count = 0
    for destaque in destaques_para_remover:
        if destaque.imagem_filename:
            try:
                caminho_imagem = os.path.join(
                    current_app.root_path, 'static/fotos_colaboradores', destaque.imagem_filename
                )
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
            except Exception as e:
                print(f"Erro ao remover imagem {destaque.imagem_filename}: {e}")
        db.session.delete(destaque)
        count += 1

    db.session.commit()
    return jsonify({'success': True, 'message': f'{count} destaque(s) removido(s) com sucesso.'})


@admin.route('/destaques/editar/<int:id>', methods=['POST'])
@login_required
@admin_required
def editar_destaque(id):
    destaque = Destaque.query.get_or_404(id)
    if 'imagem_destaque' in request.files:
        imagem_enviada = request.files['imagem_destaque']
        if imagem_enviada.filename != '':
            if destaque.imagem_filename:
                caminho_antigo = os.path.join(
                    current_app.root_path, 'static/fotos_colaboradores', destaque.imagem_filename
                )
                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)
            destaque.imagem_filename = salvar_foto(imagem_enviada)
    destaque.titulo = request.form.get('titulo')
    destaque.colaborador_id = int(request.form.get('colaborador_id'))
    destaque.descricao = request.form.get('descricao')
    destaque.mes = int(request.form.get('mes'))
    destaque.ano = int(request.form.get('ano'))
    db.session.commit()
    destaque_json = {
        'id': destaque.id,
        'titulo': destaque.titulo,
        'descricao': destaque.descricao,
        'mes': destaque.mes,
        'ano': destaque.ano,
        'imagem_filename': destaque.imagem_filename,
        'colaborador_id': destaque.colaborador_id,
        'colaborador_nome': f"{destaque.colaborador.nome} {destaque.colaborador.sobrenome}",
        'colaborador_foto': destaque.colaborador.foto_filename,
        'departamento_id': destaque.colaborador.departamento_id,
    }
    return jsonify({'success': True, 'destaque': destaque_json})
