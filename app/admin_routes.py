import pandas as pd
import io
import os
import secrets
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app, jsonify
from flask_login import login_required
from app import db
from app.models import Colaborador, Aviso, Destaque
from datetime import datetime

admin = Blueprint('admin', __name__, url_prefix='/admin')


# --- NOVA FUNÇÃO HELPER PARA SALVAR A FOTO ---
# Esta função é responsável por salvar o arquivo de imagem de forma segura
def salvar_foto(form_foto):
    # Gera um nome de arquivo aleatório e seguro para evitar conflitos
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_foto.filename)
    foto_filename = random_hex + f_ext
    # Define o caminho completo para onde a foto será salva
    foto_path = os.path.join(current_app.root_path,
                             'static/fotos_colaboradores', foto_filename)

    # Cria a pasta 'fotos_colaboradores' se ela não existir
    os.makedirs(os.path.dirname(foto_path), exist_ok=True)

    # Salva o arquivo da foto no caminho definido
    form_foto.save(foto_path)

    return foto_filename


# --- Rota para listar colaboradores (sem alterações) ---
@admin.route('/colaboradores')
@login_required
def listar_colaboradores():
    colaboradores_objetos = Colaborador.query.all()

    
    colaboradores_json = []
    for col in colaboradores_objetos:
        colaboradores_json.append({
            'id': col.id,
            'nome': col.nome,
            'sobrenome': col.sobrenome,
            'email_corporativo': col.email_corporativo
            
        })
 
    return render_template('admin/listar_colaboradores.html', colaboradores=colaboradores_json)


@admin.route('/colaboradores/gerenciar')
@login_required
def gerenciar_colaboradores():
    return render_template('admin/gerenciar_colaboradores.html')

# --- Rota para ADICIONAR um colaborador (CORRIGIDA) ---


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

    if not nome or not sobrenome or not email or not data_nascimento or not senha:
        flash('Todos os campos, exceto Cargo e Time, são obrigatórios.', 'danger')
        return redirect(url_for('admin.gerenciar_colaboradores'))

    if Colaborador.query.filter_by(email_corporativo=email).first():
        flash('Este e-mail já está cadastrado.', 'warning')
        return redirect(url_for('admin.gerenciar_colaboradores'))

    # --- Lógica de Upload da Foto (CORRIGIDA) ---
    foto_filename = None  # Começa com None por defeito
    if 'foto' in request.files:
        foto_enviada = request.files['foto']
        if foto_enviada.filename != '':
            # Se um arquivo foi enviado, chama a função para salvar e obtém o nome do arquivo
            foto_filename = salvar_foto(foto_enviada)
    # ----------------------------------------------

    novo_colaborador = Colaborador(
        nome=nome,
        sobrenome=sobrenome,
        email_corporativo=email,
        data_nascimento=pd.to_datetime(data_nascimento).date(),
        cargo=cargo,
        time=time,
        foto_filename=foto_filename  # Salva o nome do arquivo no banco de dados
    )
    novo_colaborador.set_password(senha)
    db.session.add(novo_colaborador)
    db.session.commit()

    flash('Colaborador adicionado com sucesso!', 'success')
    return redirect(url_for('admin.listar_colaboradores'))


# --- Resto das suas rotas (importar, remover, editar, etc.) ---
# ... (o seu código para as outras rotas continua aqui) ...

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
                    return redirect(url_for('admin.gerenciar_colaboradores'))

                for index, row in df.iterrows():
                    if not Colaborador.query.filter_by(email_corporativo=row['email_corporativo']).first():
                        novo_colaborador = Colaborador(
                            nome=row['nome'],
                            sobrenome=row['sobrenome'],
                            email_corporativo=row['email_corporativo'],
                            data_nascimento=pd.to_datetime(
                                row['data_nascimento']).date(),
                            cargo=row['cargo'],
                            time=row['time']
                        )
                        novo_colaborador.set_password(str(row['senha']))
                        db.session.add(novo_colaborador)

                db.session.commit()
                flash('Colaboradores importados com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Ocorreu um erro ao importar: {e}', 'danger')
        else:
            flash('Arquivo inválido. Por favor, envie uma planilha .xlsx.', 'danger')
    return redirect(url_for('admin.listar_colaboradores'))


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


@admin.route('/colaboradores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)

    if request.method == 'POST':
        # ---- LÓGICA PARA ATUALIZAR A FOTO ----
        if 'foto' in request.files:
            foto_enviada = request.files['foto']
            if foto_enviada.filename != '':
                # (Opcional, mas recomendado: apagar a foto antiga para não ocupar espaço)
                if colaborador.foto_filename:
                    foto_antiga_path = os.path.join(
                        current_app.root_path, 'static/fotos_colaboradores', colaborador.foto_filename)
                    if os.path.exists(foto_antiga_path):
                        os.remove(foto_antiga_path)

                # Salva a nova foto e atualiza o nome do arquivo no banco
                foto_filename = salvar_foto(foto_enviada)
                colaborador.foto_filename = foto_filename

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
    # Busca todos os destaques, do mais novo para o mais antigo
    destaques = Destaque.query.order_by(
        Destaque.ano.desc(), Destaque.mes.desc()).all()
    # Busca todos os colaboradores para preencher a lista de seleção
    colaboradores = Colaborador.query.order_by(Colaborador.nome).all()
    return render_template('admin/gerenciar_destaques.html', destaques=destaques, colaboradores=colaboradores)


@admin.route('/destaques/adicionar', methods=['POST'])
@login_required
def adicionar_destaque():
    titulo = request.form.get('titulo')
    colaborador_id = request.form.get('colaborador_id')
    descricao = request.form.get('descricao')

    # --- LÓGICA PARA DATA OPCIONAL ---
    mes_form = request.form.get('mes')
    ano_form = request.form.get('ano')

    # Se o mês e o ano não forem fornecidos, usa a data atual
    if mes_form and ano_form:
        mes = int(mes_form)
        ano = int(ano_form)
    else:
        hoje = datetime.utcnow()
        mes = hoje.month
        ano = hoje.year
    # ---------------------------------

    if not titulo or not colaborador_id:
        flash('Título e Colaborador são obrigatórios.', 'danger')
        return redirect(url_for('admin.gerenciar_destaques'))

    # Processa o upload do certificado, se existir
    certificado_filename = None
    if 'certificado' in request.files:
        certificado_enviado = request.files['certificado']
        if certificado_enviado.filename != '':
            certificado_filename = salvar_foto(certificado_enviado)

    novo_destaque = Destaque(
        titulo=titulo,
        colaborador_id=colaborador_id,
        descricao=descricao,
        mes=mes,
        ano=ano,
        certificado_filename=certificado_filename
    )
    db.session.add(novo_destaque)
    db.session.commit()
    flash('Destaque adicionado com sucesso!', 'success')
    return redirect(url_for('admin.gerenciar_destaques'))


@admin.route('/destaques/remover/<int:id>')
@login_required
def remover_destaque(id):
    destaque = Destaque.query.get_or_404(id)
    # (Opcional, mas recomendado: apagar o arquivo do certificado se ele existir)
    if destaque.certificado_filename:
        caminho_certificado = os.path.join(
            current_app.root_path, 'static/fotos_colaboradores', destaque.certificado_filename)
        if os.path.exists(caminho_certificado):
            os.remove(caminho_certificado)

    db.session.delete(destaque)
    db.session.commit()
    flash('Destaque removido com sucesso.', 'info')
    return redirect(url_for('admin.gerenciar_destaques'))
