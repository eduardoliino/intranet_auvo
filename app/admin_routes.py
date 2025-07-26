import pandas as pd
import io
import os
import secrets
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Colaborador, Aviso, Destaque, FaqCategoria, FaqPergunta, Ouvidoria, Evento
from datetime import datetime

admin = Blueprint('admin', __name__, url_prefix='/admin')


def salvar_foto(form_foto):

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_foto.filename)
    foto_filename = random_hex + f_ext

    foto_path = os.path.join(current_app.root_path,
                             'static/fotos_colaboradores', foto_filename)

    os.makedirs(os.path.dirname(foto_path), exist_ok=True)

    form_foto.save(foto_path)

    return foto_filename


# --- Rota para listar colaboradores (sem alterações) ---
@admin.route('/colaboradores')
@login_required
def listar_colaboradores():
    colaboradores_objetos = Colaborador.query.order_by(Colaborador.nome).all()
    # Converte os objetos para um formato compatível com JSON para o Alpine.js
    colaboradores_json = [{'id': c.id, 'nome': c.nome, 'sobrenome': c.sobrenome,
                           'email_corporativo': c.email_corporativo} for c in colaboradores_objetos]
    return render_template('admin/listar_colaboradores.html', colaboradores=colaboradores_json)

# Rota para a página do formulário de cadastro manual


@admin.route('/colaboradores/adicionar-manual', methods=['GET'])
@login_required
def adicionar_colaborador_manual_form():
    return render_template('admin/adicionar_colaborador_manual.html')

# Rota que processa o envio do formulário manual


@admin.route('/colaboradores/adicionar', methods=['POST'])
@login_required
def adicionar_colaborador():
    nome = request.form.get('nome')
    sobrenome = request.form.get('sobrenome')
    email = request.form.get('email_corporativo')
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

# Rota para a página do formulário de importação


@admin.route('/colaboradores/importar-planilha', methods=['GET'])
@login_required
def importar_colaboradores_form():
    return render_template('admin/importar_colaboradores.html')

# Rota que processa o upload da planilha


@admin.route('/colaboradores/importar', methods=['POST'])
@login_required
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

# Rota para baixar a planilha modelo


@admin.route('/colaboradores/baixar_modelo')
@login_required
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

# Rota para a página de edição de um colaborador


@admin.route('/colaboradores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)

    if request.method == 'POST':
        # --- LÓGICA PARA ATUALIZAR A FOTO ---
        if 'foto' in request.files:
            foto_enviada = request.files['foto']
            if foto_enviada.filename != '':
                # Se uma imagem antiga existir, apaga-a do servidor
                if colaborador.foto_filename:
                    foto_antiga_path = os.path.join(
                        current_app.root_path, 'static/fotos_colaboradores', colaborador.foto_filename)
                    if os.path.exists(foto_antiga_path):
                        os.remove(foto_antiga_path)

                # Salva a nova imagem e atualiza o nome no banco de dados
                colaborador.foto_filename = salvar_foto(foto_enviada)

        # --- ATUALIZA OS DADOS DO COLABORADOR ---
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

    # Garante que o template de EDIÇÃO é renderizado para a requisição GET
    return render_template('admin/edit_colaborador.html', colaborador=colaborador)


# Rota para remover um colaborador


@admin.route('/colaboradores/remover/<int:id>')
@login_required
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

# Rota para remover todos os colaboradores


@admin.route('/colaboradores/remover_todos', methods=['POST'])
@login_required
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
def gerenciar_avisos():
    # Busca todos os avisos para a carga inicial
    avisos_objetos = Aviso.query.order_by(Aviso.id.desc()).all()
    # Converte para um formato compatível com JSON para o Alpine.js
    avisos_json = [{
        'id': aviso.id,
        'titulo': aviso.titulo,
        'conteudo': aviso.conteudo,
        'link_url': aviso.link_url,
        'link_texto': aviso.link_texto
    } for aviso in avisos_objetos]
    return render_template('admin/gerenciar_avisos.html', avisos=avisos_json)


@admin.route('/avisos/adicionar', methods=['POST'])
@login_required
def adicionar_aviso():
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
        link_texto=link_texto
    )
    db.session.add(novo_aviso)
    db.session.commit()

    # Devolve os dados do aviso criado em formato JSON
    return jsonify({
        'success': True,
        'aviso': {
            'id': novo_aviso.id,
            'titulo': novo_aviso.titulo,
            'conteudo': novo_aviso.conteudo,
            'link_url': novo_aviso.link_url,
            'link_texto': novo_aviso.link_texto
        }
    })


@admin.route('/avisos/remover/<int:id>', methods=['DELETE'])
@login_required
def remover_aviso(id):
    aviso = Aviso.query.get_or_404(id)
    db.session.delete(aviso)
    db.session.commit()
    # Devolve uma resposta de sucesso em JSON
    return jsonify({'success': True, 'message': 'Aviso removido com sucesso.'})


@admin.route('/destaques')
@login_required
def gerenciar_destaques():
    destaques_obj = Destaque.query.order_by(
        Destaque.ano.desc(), Destaque.mes.desc()).all()
    colaboradores_obj = Colaborador.query.order_by(Colaborador.nome).all()

    # Converte os dados para um formato compatível com JSON
    destaques_json = [{
        'id': d.id, 'titulo': d.titulo, 'descricao': d.descricao, 'mes': d.mes, 'ano': d.ano,
        'imagem_filename': d.imagem_filename,
        'colaborador_id': d.colaborador_id,
        'colaborador_nome': f"{d.colaborador.nome} {d.colaborador.sobrenome}",
        'colaborador_foto': d.colaborador.foto_filename
    } for d in destaques_obj]
    colaboradores_json = [
        {'id': c.id, 'nome': f"{c.nome} {c.sobrenome}"} for c in colaboradores_obj]

    # ---- CORREÇÃO: Pega todos os anos únicos que existem nos destaques ----
    anos_disponiveis = sorted(
        list(set(d.ano for d in destaques_obj)), reverse=True)

    return render_template(
        'admin/gerenciar_destaques.html',
        destaques=destaques_json,
        colaboradores=colaboradores_json,
        anos=anos_disponiveis  # Envia a lista de anos para o template
    )


@admin.route('/destaques/adicionar', methods=['POST'])
@login_required
def adicionar_destaque():
    # --- Lógica principal (que estava em falta) ---
    titulo = request.form.get('titulo')
    colaborador_id = request.form.get('colaborador_id')
    descricao = request.form.get('descricao')

    # Lógica para data opcional
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

    # Processa o upload da imagem
    imagem_filename = None
    if 'imagem_destaque' in request.files:
        imagem_enviada = request.files['imagem_destaque']
        if imagem_enviada.filename != '':
            imagem_filename = salvar_foto(imagem_enviada)

    # Cria o novo objeto no banco de dados
    novo_destaque = Destaque(
        titulo=titulo,
        colaborador_id=int(colaborador_id),
        descricao=descricao,
        mes=mes,
        ano=ano,
        imagem_filename=imagem_filename
    )
    db.session.add(novo_destaque)
    db.session.commit()
    # ----------------------------------------------

    # No final, depois do db.session.commit(), devolva o objeto completo
    destaque_json = {
        'id': novo_destaque.id,
        'titulo': novo_destaque.titulo,
        'descricao': novo_destaque.descricao,
        'mes': novo_destaque.mes,
        'ano': novo_destaque.ano,
        'imagem_filename': novo_destaque.imagem_filename,
        'colaborador_id': novo_destaque.colaborador_id,
        'colaborador_nome': f"{novo_destaque.colaborador.nome} {novo_destaque.colaborador.sobrenome}",
        'colaborador_foto': novo_destaque.colaborador.foto_filename
    }
    return jsonify({'success': True, 'destaque': destaque_json})


@admin.route('/destaques/remover/<int:id>', methods=['DELETE'])
@login_required
def remover_destaque(id):
    # Esta rota também precisa de ser convertida para devolver JSON
    destaque = Destaque.query.get_or_404(id)
    if destaque.imagem_filename:
        caminho_imagem = os.path.join(
            current_app.root_path, 'static/fotos_colaboradores', destaque.imagem_filename)
        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)
    db.session.delete(destaque)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Destaque removido com sucesso.'})

# --- NOVA ROTA PARA EDITAR UM DESTAQUE ---


@admin.route('/destaques/editar/<int:id>', methods=['POST'])
@login_required
def editar_destaque(id):
    destaque = Destaque.query.get_or_404(id)

    # --- LÓGICA PARA ATUALIZAR A IMAGEM (CORRIGIDA) ---
    if 'imagem_destaque' in request.files:
        imagem_enviada = request.files['imagem_destaque']
        if imagem_enviada.filename != '':
            # Se uma imagem antiga existir, apaga-a do servidor
            if destaque.imagem_filename:
                caminho_antigo = os.path.join(
                    current_app.root_path, 'static/fotos_colaboradores', destaque.imagem_filename)
                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)

            # Salva a nova imagem e atualiza o nome no banco de dados
            destaque.imagem_filename = salvar_foto(imagem_enviada)
    # ---------------------------------------------------

    destaque.titulo = request.form.get('titulo')
    destaque.colaborador_id = int(request.form.get('colaborador_id'))
    destaque.descricao = request.form.get('descricao')
    destaque.mes = int(request.form.get('mes'))
    destaque.ano = int(request.form.get('ano'))

    db.session.commit()

    # Devolve o objeto atualizado para o JavaScript
    destaque_json = {
        'id': destaque.id, 'titulo': destaque.titulo, 'descricao': destaque.descricao,
        'mes': destaque.mes, 'ano': destaque.ano, 'imagem_filename': destaque.imagem_filename,
        'colaborador_id': destaque.colaborador_id,
        'colaborador_nome': f"{destaque.colaborador.nome} {destaque.colaborador.sobrenome}",
        'colaborador_foto': destaque.colaborador.foto_filename
    }
    return jsonify({'success': True, 'destaque': destaque_json})


@admin.route('/faq/gerenciar')
@login_required
def gerenciar_faq():
    categorias_obj = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    perguntas_obj = FaqPergunta.query.order_by(FaqPergunta.id.desc()).all()

    # Converte os dados para um formato compatível com JSON
    categorias_json = [{'id': cat.id, 'nome': cat.nome}
                       for cat in categorias_obj]
    perguntas_json = [{
        'id': p.id,
        'pergunta': p.pergunta,
        'resposta': p.resposta,
        'palavras_chave': p.palavras_chave,
        'categoria_id': p.categoria_id,
        # Adiciona o nome da categoria para facilitar a exibição
        'categoria_nome': p.categoria.nome
    } for p in perguntas_obj]

    return render_template('admin/gerenciar_faq.html', categorias=categorias_json, perguntas=perguntas_json)


@admin.route('/faq/categorias/adicionar', methods=['POST'])
@login_required
def adicionar_categoria_faq():
    nome = request.form.get('nome')
    if not nome:
        return jsonify({'success': False, 'message': 'O nome da categoria é obrigatório.'}), 400
    if FaqCategoria.query.filter_by(nome=nome).first():
        return jsonify({'success': False, 'message': 'Essa categoria já existe.'}), 400

    nova_categoria = FaqCategoria(nome=nome)
    db.session.add(nova_categoria)
    db.session.commit()
    return jsonify({'success': True, 'categoria': {'id': nova_categoria.id, 'nome': nova_categoria.nome}})


@admin.route('/faq/categorias/remover/<int:id>', methods=['DELETE'])
@login_required
def remover_categoria_faq(id):
    categoria = FaqCategoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Categoria removida com sucesso.'})


@admin.route('/faq/perguntas/adicionar', methods=['POST'])
@login_required
def adicionar_pergunta_faq():
    data = request.form
    if not data.get('pergunta') or not data.get('resposta') or not data.get('categoria_id'):
        return jsonify({'success': False, 'message': 'Pergunta, resposta e categoria são campos obrigatórios.'}), 400

    nova_pergunta = FaqPergunta(
        pergunta=data.get('pergunta'),
        resposta=data.get('resposta'),
        categoria_id=int(data.get('categoria_id')),
        palavras_chave=data.get('palavras_chave'),
        link_url=data.get('link_url'),
        link_texto=data.get('link_texto')
    )
    db.session.add(nova_pergunta)
    db.session.commit()

    pergunta_json = {
        'id': nova_pergunta.id,
        'pergunta': nova_pergunta.pergunta,
        'resposta': nova_pergunta.resposta,
        'palavras_chave': nova_pergunta.palavras_chave,
        'categoria_id': nova_pergunta.categoria_id,
        'categoria_nome': nova_pergunta.categoria.nome
    }
    return jsonify({'success': True, 'pergunta': pergunta_json})


@admin.route('/faq/perguntas/remover/<int:id>', methods=['DELETE'])
@login_required
def remover_pergunta_faq(id):
    pergunta = FaqPergunta.query.get_or_404(id)
    db.session.delete(pergunta)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Pergunta removida com sucesso.'})


@admin.route('/faq/perguntas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
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
def gerenciar_ouvidoria():
    entradas_obj = Ouvidoria.query.order_by(Ouvidoria.data_envio.desc()).all()

    entradas_json = [{
        'id': e.id,
        'data_envio': e.data_envio.isoformat(),
        'tipo_denuncia': e.tipo_denuncia,
        'mensagem': e.mensagem,
        'anonima': e.anonima,
        'nome': e.nome,
        'contato': e.contato,
        'status': e.status
    } for e in entradas_obj]

    return render_template('admin/gerenciar_ouvidoria.html', entradas=entradas_json)


@admin.route('/ouvidoria/atualizar_status/<int:id>', methods=['POST'])
@login_required
def atualizar_status_ouvidoria(id):
    entrada = Ouvidoria.query.get_or_404(id)
    data = request.get_json()
    novo_status = data.get('status')

    if novo_status in ['Nova', 'Em análise', 'Resolvida']:
        entrada.status = novo_status
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Status inválido.'}), 400

# Rota para renderizar a página do calendário


@admin.route('/calendario')
@login_required
def calendario():
    return render_template('admin/calendario.html', title='Calendário de Eventos')

# Rota de API para fornecer os eventos em formato JSON


@admin.route('/calendario/eventos')
@login_required
def calendario_eventos():
    eventos = Evento.query.all()
    eventos_json = [evento.to_dict() for evento in eventos]
    return jsonify(eventos_json)


@admin.route('/calendario/eventos/novo', methods=['POST'])
@login_required
def novo_evento():
    data = request.get_json()
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
    return jsonify({'success': True, 'id': novo_evento.id})


@admin.route('/calendario/eventos/editar/<int:id>', methods=['PUT'])
@login_required
def editar_evento(id):
    evento = Evento.query.get_or_404(id)
    data = request.get_json()
    evento.title = data['title']
    evento.start = datetime.fromisoformat(data['start'])
    evento.end = datetime.fromisoformat(
        data['end']) if data.get('end') else None
    evento.description = data.get('description')
    evento.location = data.get('location')
    evento.color = data.get('color')
    db.session.commit()
    return jsonify({'success': True})


@admin.route('/calendario/eventos/remover/<int:id>', methods=['DELETE'])
@login_required
def remover_evento(id):
    evento = Evento.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    return jsonify({'success': True})
