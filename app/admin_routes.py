import pandas as pd
import io
import os
import secrets
from functools import wraps
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Colaborador, Aviso, Destaque, FaqCategoria, FaqPergunta, Ouvidoria, Evento
from datetime import datetime

admin = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def salvar_foto(form_foto):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_foto.filename)
    foto_filename = random_hex + f_ext
    foto_path = os.path.join(current_app.root_path,
                             'static/fotos_colaboradores', foto_filename)
    os.makedirs(os.path.dirname(foto_path), exist_ok=True)
    form_foto.save(foto_path)
    return foto_filename


@admin.route('/colaboradores')
@login_required
@admin_required
def listar_colaboradores():
    colaboradores_objetos = Colaborador.query.order_by(Colaborador.nome).all()
    colaboradores_json = [{'id': c.id, 'nome': c.nome, 'sobrenome': c.sobrenome,
                           'email_corporativo': c.email_corporativo} for c in colaboradores_objetos]
    return render_template('admin/listar_colaboradores.html', colaboradores=colaboradores_json, total_colaboradores=len(colaboradores_objetos))


@admin.route('/colaboradores/adicionar-manual', methods=['GET'])
@login_required
@admin_required
def adicionar_colaborador_manual_form():
    return render_template('admin/adicionar_colaborador_manual.html')


@admin.route('/colaboradores/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_colaborador():
    email = request.form.get('email_corporativo')
    colaborador_existente = Colaborador.query.filter_by(
        email_corporativo=email).first()
    if colaborador_existente:
        flash(
            f'O e-mail "{email}" já está em uso por outro colaborador.', 'danger')
        return redirect(url_for('admin.adicionar_colaborador_manual_form'))

    nome = request.form.get('nome')
    sobrenome = request.form.get('sobrenome')
    data_nascimento = request.form.get('data_nascimento')
    cargo = request.form.get('cargo')
    time = request.form.get('time')
    senha = request.form.get('senha')
    foto_filename = None
    if 'foto' in request.files:
        foto_enviada = request.files['foto']
        if foto_enviada.filename != '':
            foto_filename = salvar_foto(foto_enviada)

    novo_colaborador = Colaborador(
        nome=nome, sobrenome=sobrenome, email_corporativo=email,
        data_nascimento=pd.to_datetime(data_nascimento).date(),
        cargo=cargo, time=time, foto_filename=foto_filename
    )
    novo_colaborador.set_password(senha)
    db.session.add(novo_colaborador)
    db.session.commit()
    flash('Colaborador adicionado com sucesso!', 'success')
    return redirect(url_for('admin.listar_colaboradores'))


@admin.route('/colaboradores/importar-planilha', methods=['GET'])
@login_required
@admin_required
def importar_colaboradores_form():
    return render_template('admin/importar_colaboradores.html')


@admin.route('/colaboradores/importar', methods=['POST'])
@login_required
@admin_required
def importar_colaboradores():
    if 'planilha_colaboradores' in request.files:
        arquivo = request.files['planilha_colaboradores']
        if arquivo.filename != '' and arquivo.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(arquivo)
                colunas_necessarias = [
                    'nome', 'sobrenome', 'email_corporativo', 'data_nascimento', 'cargo', 'time', 'senha']
                if not all(coluna in df.columns for coluna in colunas_necessarias):
                    flash(
                        'A planilha não contém todas as colunas necessárias.', 'danger')
                    return redirect(url_for('admin.importar_colaboradores_form'))

                for index, row in df.iterrows():
                    if not Colaborador.query.filter_by(email_corporativo=row['email_corporativo']).first():
                        novo_colaborador = Colaborador(
                            nome=row['nome'], sobrenome=row['sobrenome'],
                            email_corporativo=row['email_corporativo'],
                            data_nascimento=pd.to_datetime(
                                row['data_nascimento']).date(),
                            cargo=row.get('cargo'), time=row.get('time')
                        )
                        novo_colaborador.set_password(str(row['senha']))
                        db.session.add(novo_colaborador)
                db.session.commit()
                flash('Colaboradores importados com sucesso!', 'success')
            except Exception as e:
                flash(f'Ocorreu um erro ao importar: {e}', 'danger')
    return redirect(url_for('admin.listar_colaboradores'))


@admin.route('/colaboradores/baixar_modelo')
@login_required
@admin_required
def baixar_modelo_planilha():
    colunas = ['nome', 'sobrenome', 'email_corporativo',
               'data_nascimento', 'cargo', 'time', 'senha']
    df_modelo = pd.DataFrame(columns=colunas)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False, sheet_name='colaboradores')
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name='modelo_importacao_colaboradores.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@admin.route('/colaboradores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)
    if request.method == 'POST':
        if 'foto' in request.files:
            foto_enviada = request.files['foto']
            if foto_enviada.filename != '':
                if colaborador.foto_filename:
                    foto_antiga_path = os.path.join(
                        current_app.root_path, 'static/fotos_colaboradores', colaborador.foto_filename)
                    if os.path.exists(foto_antiga_path):
                        os.remove(foto_antiga_path)
                colaborador.foto_filename = salvar_foto(foto_enviada)

        colaborador.nome = request.form.get('nome')
        colaborador.sobrenome = request.form.get('sobrenome')
        colaborador.email_corporativo = request.form.get('email_corporativo')
        colaborador.cargo = request.form.get('cargo')
        colaborador.time = request.form.get('time')
        colaborador.data_nascimento = pd.to_datetime(
            request.form.get('data_nascimento')).date()
        nova_senha = request.form.get('senha')
        if nova_senha:
            colaborador.set_password(nova_senha)
        try:
            db.session.commit()
            flash('Colaborador atualizado com sucesso!', 'success')
            return redirect(url_for('admin.listar_colaboradores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar o colaborador: {e}', 'danger')
    return render_template('admin/edit_colaborador.html', colaborador=colaborador)


@admin.route('/colaboradores/remover/<int:id>')
@login_required
@admin_required
def remover_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)
    try:
        db.session.delete(colaborador)
        db.session.commit()
        flash('Colaborador removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover colaborador: {e}', 'danger')
    return redirect(url_for('admin.listar_colaboradores'))


@admin.route('/colaboradores/remover_todos', methods=['POST'])
@login_required
@admin_required
def remover_todos_colaboradores():
    confirmacao = request.form.get('confirmacao')
    if confirmacao == 'confirmar exclusão':
        try:
            num_rows_deleted = db.session.query(Colaborador).delete()
            db.session.commit()
            flash(
                f'{num_rows_deleted} colaboradores foram removidos com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(
                f'Ocorreu um erro ao remover os colaboradores: {e}', 'danger')
    else:
        flash('A confirmação digitada está incorreta. Nenhuma ação foi tomada.', 'warning')
    return redirect(url_for('admin.listar_colaboradores'))


@admin.route('/avisos')
@login_required
@admin_required
def gerenciar_avisos():
    total_colaboradores = Colaborador.query.count()
    avisos_objetos = Aviso.query.order_by(Aviso.id.desc()).all()
    avisos_json = [{'id': aviso.id, 'titulo': aviso.titulo, 'conteudo': aviso.conteudo,
                    'link_url': aviso.link_url, 'link_texto': aviso.link_texto} for aviso in avisos_objetos]
    return render_template('admin/gerenciar_avisos.html', avisos=avisos_json, total_colaboradores=total_colaboradores)


@admin.route('/avisos/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_aviso():
    titulo = request.form.get('titulo')
    conteudo = request.form.get('conteudo')
    link_url = request.form.get('link_url')
    link_texto = request.form.get('link_texto')
    if not titulo or not conteudo:
        return jsonify({'success': False, 'message': 'Título e conteúdo são obrigatórios.'}), 400
    novo_aviso = Aviso(titulo=titulo, conteudo=conteudo,
                       link_url=link_url, link_texto=link_texto)
    db.session.add(novo_aviso)
    db.session.commit()
    return jsonify({'success': True, 'aviso': {'id': novo_aviso.id, 'titulo': novo_aviso.titulo, 'conteudo': novo_aviso.conteudo, 'link_url': novo_aviso.link_url, 'link_texto': novo_aviso.link_texto}})


@admin.route('/avisos/remover/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def remover_aviso(id):
    aviso = Aviso.query.get_or_404(id)
    db.session.delete(aviso)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Aviso removido com sucesso.'})


@admin.route('/destaques')
@login_required
@admin_required
def gerenciar_destaques():
    total_colaboradores = Colaborador.query.count()
    destaques_obj = Destaque.query.order_by(
        Destaque.ano.desc(), Destaque.mes.desc()).all()
    colaboradores_obj = Colaborador.query.order_by(Colaborador.nome).all()
    destaques_json = [{'id': d.id, 'titulo': d.titulo, 'descricao': d.descricao, 'mes': d.mes, 'ano': d.ano, 'imagem_filename': d.imagem_filename, 'colaborador_id': d.colaborador_id,
                       'colaborador_nome': f"{d.colaborador.nome} {d.colaborador.sobrenome}", 'colaborador_foto': d.colaborador.foto_filename} for d in destaques_obj]
    colaboradores_json = [
        {'id': c.id, 'nome': f"{c.nome} {c.sobrenome}"} for c in colaboradores_obj]
    anos_disponiveis = sorted(
        list(set(d.ano for d in destaques_obj)), reverse=True)
    return render_template('admin/gerenciar_destaques.html', destaques=destaques_json, colaboradores=colaboradores_json, anos=anos_disponiveis, total_colaboradores=total_colaboradores)


@admin.route('/destaques/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_destaque():
    titulo = request.form.get('titulo')
    colaborador_id = request.form.get('colaborador_id')
    descricao = request.form.get('descricao')
    mes_form = request.form.get('mes')
    ano_form = request.form.get('ano')
    if mes_form and ano_form:
        mes = int(mes_form)
        ano = int(ano_form)
    else:
        hoje = datetime.utcnow()
        mes = hoje.month
        ano = hoje.year
    if not titulo or not colaborador_id:
        return jsonify({'success': False, 'message': 'Título e Colaborador são obrigatórios.'}), 400
    imagem_filename = None
    if 'imagem_destaque' in request.files:
        imagem_enviada = request.files['imagem_destaque']
        if imagem_enviada.filename != '':
            imagem_filename = salvar_foto(imagem_enviada)
    novo_destaque = Destaque(titulo=titulo, colaborador_id=int(
        colaborador_id), descricao=descricao, mes=mes, ano=ano, imagem_filename=imagem_filename)
    db.session.add(novo_destaque)
    db.session.commit()
    destaque_json = {'id': novo_destaque.id, 'titulo': novo_destaque.titulo, 'descricao': novo_destaque.descricao, 'mes': novo_destaque.mes, 'ano': novo_destaque.ano, 'imagem_filename': novo_destaque.imagem_filename,
                     'colaborador_id': novo_destaque.colaborador_id, 'colaborador_nome': f"{novo_destaque.colaborador.nome} {novo_destaque.colaborador.sobrenome}", 'colaborador_foto': novo_destaque.colaborador.foto_filename}
    return jsonify({'success': True, 'destaque': destaque_json})


@admin.route('/destaques/remover/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def remover_destaque(id):
    destaque = Destaque.query.get_or_404(id)
    if destaque.imagem_filename:
        caminho_imagem = os.path.join(
            current_app.root_path, 'static/fotos_colaboradores', destaque.imagem_filename)
        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)
    db.session.delete(destaque)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Destaque removido com sucesso.'})


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
                    current_app.root_path, 'static/fotos_colaboradores', destaque.imagem_filename)
                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)
            destaque.imagem_filename = salvar_foto(imagem_enviada)
    destaque.titulo = request.form.get('titulo')
    destaque.colaborador_id = int(request.form.get('colaborador_id'))
    destaque.descricao = request.form.get('descricao')
    destaque.mes = int(request.form.get('mes'))
    destaque.ano = int(request.form.get('ano'))
    db.session.commit()
    destaque_json = {'id': destaque.id, 'titulo': destaque.titulo, 'descricao': destaque.descricao, 'mes': destaque.mes, 'ano': destaque.ano, 'imagem_filename': destaque.imagem_filename,
                     'colaborador_id': destaque.colaborador_id, 'colaborador_nome': f"{destaque.colaborador.nome} {destaque.colaborador.sobrenome}", 'colaborador_foto': destaque.colaborador.foto_filename}
    return jsonify({'success': True, 'destaque': destaque_json})


@admin.route('/faq/gerenciar')
@login_required
@admin_required
def gerenciar_faq():
    total_colaboradores = Colaborador.query.count()
    perguntas_obj = FaqPergunta.query.order_by(FaqPergunta.id.desc()).all()
    perguntas_json = [{'id': p.id, 'pergunta': p.pergunta, 'resposta': p.resposta,
                       'categoria_nome': p.categoria.nome} for p in perguntas_obj]
    return render_template('admin/gerenciar_faq.html', perguntas=perguntas_json, total_colaboradores=total_colaboradores)


@admin.route('/faq/categorias', methods=['GET'])
@login_required
@admin_required
def gerenciar_categorias_faq():
    categorias = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    return render_template('admin/gerenciar_faq_categorias.html', categorias=categorias)


@admin.route('/faq/categorias/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_categoria_faq():
    nome = request.form.get('nome')
    if nome and not FaqCategoria.query.filter_by(nome=nome).first():
        nova_categoria = FaqCategoria(nome=nome)
        db.session.add(nova_categoria)
        db.session.commit()
        flash('Categoria adicionada com sucesso!', 'success')
    else:
        flash('Nome de categoria inválido ou já existente.', 'danger')
    return redirect(url_for('admin.gerenciar_categorias_faq'))


@admin.route('/faq/categorias/remover/<int:id>')
@login_required
@admin_required
def remover_categoria_faq(id):
    categoria = FaqCategoria.query.get_or_404(id)
    if categoria.perguntas:
        flash('Não é possível remover uma categoria que contém perguntas.', 'danger')
    else:
        db.session.delete(categoria)
        db.session.commit()
        flash('Categoria removida com sucesso.', 'success')
    return redirect(url_for('admin.gerenciar_categorias_faq'))


@admin.route('/faq/perguntas/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def adicionar_pergunta_faq():
    categorias = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    if request.method == 'POST':
        data = request.form
        if not data.get('pergunta') or not data.get('resposta') or not data.get('categoria_id'):
            flash('Pergunta, resposta e categoria são campos obrigatórios.', 'danger')
            return redirect(url_for('admin.adicionar_pergunta_faq'))
        nova_pergunta = FaqPergunta(pergunta=data.get('pergunta'), resposta=data.get('resposta'), categoria_id=int(data.get(
            'categoria_id')), palavras_chave=data.get('palavras_chave'), link_url=data.get('link_url'), link_texto=data.get('link_texto'))
        db.session.add(nova_pergunta)
        db.session.commit()
        flash('Pergunta adicionada com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_faq'))
    return render_template('admin/adicionar_faq_pergunta.html', categorias=categorias)


@admin.route('/faq/perguntas/remover/<int:id>')
@login_required
@admin_required
def remover_pergunta_faq(id):
    pergunta = FaqPergunta.query.get_or_404(id)
    db.session.delete(pergunta)
    db.session.commit()
    flash('Pergunta removida com sucesso!', 'success')
    return redirect(url_for('admin.gerenciar_faq'))


@admin.route('/faq/perguntas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
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


@admin.route('/ouvidoria')
@login_required
@admin_required
def gerenciar_ouvidoria():
    total_colaboradores = Colaborador.query.count()
    entradas_obj = Ouvidoria.query.order_by(Ouvidoria.data_envio.desc()).all()
    entradas_json = [{'id': e.id, 'data_envio': e.data_envio.isoformat(), 'tipo_denuncia': e.tipo_denuncia, 'mensagem': e.mensagem,
                      'anonima': e.anonima, 'nome': e.nome, 'contato': e.contato, 'status': e.status} for e in entradas_obj]
    return render_template('admin/gerenciar_ouvidoria.html', entradas=entradas_json, total_colaboradores=total_colaboradores)


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


@admin.route('/eventos')
@login_required
@admin_required
def gerenciar_eventos():
    total_colaboradores = Colaborador.query.count()
    eventos = Evento.query.order_by(Evento.start.desc()).all()
    eventos_json = [evento.to_dict() for evento in eventos]
    return render_template('admin/gerenciar_eventos.html', eventos=eventos_json, total_colaboradores=total_colaboradores)


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
        color=data.get('color'),
        user_id=current_user.id
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
    evento.end = datetime.fromisoformat(
        data['end']) if data.get('end') else None
    evento.description = data.get('description')
    evento.location = data.get('location')
    evento.color = data.get('color')
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
