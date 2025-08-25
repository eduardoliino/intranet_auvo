from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app import db
from app.models import FaqCategoria, FaqPergunta
from . import admin
from .utils import permission_required


@admin.route('/faq/gerenciar')
@login_required
@permission_required('gerenciar_faq')
def gerenciar_faq():
    perguntas_obj = FaqPergunta.query.order_by(FaqPergunta.id.desc()).all()
    perguntas_json = [
        {
            'id': p.id,
            'pergunta': p.pergunta,
            'resposta': p.resposta,
            'palavras_chave': p.palavras_chave,
            'categoria_nome': p.categoria.nome,
        }
        for p in perguntas_obj
    ]
    return render_template('admin/gerenciar_faq.html', perguntas=perguntas_json)


@admin.route('/faq/categorias', methods=['GET'])
@login_required
@permission_required('gerenciar_faq')
def gerenciar_categorias_faq():
    categorias_obj = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    categorias_json = [{'id': cat.id, 'nome': cat.nome} for cat in categorias_obj]
    return render_template('admin/gerenciar_faq_categorias.html', categorias=categorias_json)


@admin.route('/faq/categorias/adicionar', methods=['POST'])
@login_required
@permission_required('gerenciar_faq')
def adicionar_categoria_faq():
    data = request.json
    nome = data.get('nome')
    if not nome:
        return jsonify({'success': False, 'message': 'O nome da categoria é obrigatório.'}), 400
    if FaqCategoria.query.filter_by(nome=nome).first():
        return jsonify({'success': False, 'message': 'Esta categoria já existe.'}), 400

    nova_categoria = FaqCategoria(nome=nome)
    db.session.add(nova_categoria)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Categoria adicionada com sucesso!',
        'categoria': {'id': nova_categoria.id, 'nome': nova_categoria.nome},
    })


@admin.route('/faq/categorias/remover/<int:id>', methods=['DELETE'])
@login_required
@permission_required('gerenciar_faq')
def remover_categoria_faq(id):
    categoria = FaqCategoria.query.get_or_404(id)
    if categoria.perguntas:
        return jsonify({'success': False, 'message': 'Não é possível remover uma categoria que contém perguntas.'}), 400

    db.session.delete(categoria)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Categoria removida com sucesso.'})


@admin.route('/faq/perguntas/adicionar', methods=['GET', 'POST'])
@login_required
@permission_required('gerenciar_faq')
def adicionar_pergunta_faq():
    categorias = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    if request.method == 'POST':
        data = request.form
        if not data.get('pergunta') or not data.get('resposta') or not data.get('categoria_id'):
            flash('Pergunta, resposta e categoria são campos obrigatórios.', 'danger')
            return redirect(url_for('admin.adicionar_pergunta_faq'))
        nova_pergunta = FaqPergunta(
            pergunta=data.get('pergunta'),
            resposta=data.get('resposta'),
            categoria_id=int(data.get('categoria_id')),
            palavras_chave=data.get('palavras_chave'),
            link_url=data.get('link_url'),
            link_texto=data.get('link_texto'),
        )
        db.session.add(nova_pergunta)
        db.session.commit()
        flash('Pergunta adicionada com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_faq'))
    return render_template('admin/adicionar_faq_pergunta.html', categorias=categorias)


@admin.route('/faq/perguntas/remover/<int:id>', methods=['DELETE'])
@login_required
@permission_required('gerenciar_faq')
def remover_pergunta_faq(id):
    pergunta = FaqPergunta.query.get_or_404(id)
    db.session.delete(pergunta)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Pergunta removida com sucesso!'})


@admin.route('/faq/perguntas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('gerenciar_faq')
def editar_pergunta_faq(id):
    pergunta = FaqPergunta.query.get_or_404(id)
    categorias = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    if request.method == 'POST':
        pergunta.pergunta = request.form.get('pergunta')
        pergunta.resposta = request.form.get('resposta')
        pergunta.categoria_id = request.form.get('categoria_id')
        pergunta.palavras_chave = request.form.get('palavras_chave')
        pergunta.link_url = request.form.get('link_url')
        pergunta.link_texto = request.form.get('link_texto')
        try:
            db.session.commit()
            flash('Pergunta atualizada com sucesso!', 'success')
            return redirect(url_for('admin.gerenciar_faq'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar a pergunta: {e}', 'danger')
    return render_template('admin/edit_faq_pergunta.html', pergunta=pergunta, categorias=categorias)
