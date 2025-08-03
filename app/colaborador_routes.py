# app/colaborador_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app, jsonify
from flask_login import login_required
from app import db
from app.models import Colaborador, Cargo, Departamento
from app.admin_routes import admin_required, salvar_foto
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import pandas as pd
import io

colaborador_bp = Blueprint('colaborador', __name__,
                           url_prefix='/admin/colaboradores')


@colaborador_bp.route('/')
@admin_required
def listar():
    # A consulta agora carrega todos os colaboradores de uma vez, de forma otimizada.
    colaboradores = Colaborador.query.options(
        joinedload(Colaborador.cargo),
        joinedload(Colaborador.departamento)
    ).order_by(Colaborador.nome).all()

    # Prepara os dados para o JavaScript
    colaboradores_json = [{
        'id': c.id, 'nome': c.nome, 'sobrenome': c.sobrenome,
        'email': c.email_corporativo,
        'cargo': c.cargo.titulo if c.cargo else '-',
        'cargo_id': c.cargo_id,
        'depto': c.departamento.nome if c.departamento else '-',
        'depto_id': c.departamento_id,
        'foto': c.foto_filename
    } for c in colaboradores]

    # Carrega os filtros
    cargos = Cargo.query.order_by(Cargo.titulo).all()
    departamentos = Departamento.query.order_by(Departamento.nome).all()

    return render_template('admin/listar_colaboradores.html',
                           cargos=cargos,
                           departamentos=departamentos,
                           colaboradores_json=colaboradores_json)


@colaborador_bp.route('/adicionar', methods=['GET', 'POST'])
@admin_required
def adicionar():
    if request.method == 'POST':
        email = request.form.get('email_corporativo')
        if Colaborador.query.filter_by(email_corporativo=email).first():
            flash(f'O e-mail "{email}" já está em uso.', 'danger')
            return redirect(url_for('colaborador.adicionar'))

        foto_filename = None
        if 'foto' in request.files and request.files['foto'].filename != '':
            foto_filename = salvar_foto(request.files['foto'])

        novo_colaborador = Colaborador(
            nome=request.form.get('nome'),
            sobrenome=request.form.get('sobrenome'),
            email_corporativo=email,
            data_nascimento=pd.to_datetime(
                request.form.get('data_nascimento'), dayfirst=True).date(),
            data_inicio=pd.to_datetime(request.form.get(
                'data_inicio'), dayfirst=True).date(),
            foto_filename=foto_filename,
            cargo_id=int(request.form.get('cargo_id')
                         ) if request.form.get('cargo_id') else None,
            departamento_id=int(request.form.get('departamento_id')) if request.form.get(
                'departamento_id') else None,
            superior_id=int(request.form.get('superior_id')) if request.form.get(
                'superior_id') != 'None' else None
        )
        novo_colaborador.set_password(request.form.get('senha'))
        db.session.add(novo_colaborador)
        db.session.commit()
        flash('Colaborador adicionado com sucesso!', 'success')
        return redirect(url_for('colaborador.listar'))

    cargos = Cargo.query.order_by(Cargo.titulo).all()
    departamentos = Departamento.query.order_by(Departamento.nome).all()
    superiores = Colaborador.query.order_by(Colaborador.nome).all()
    return render_template('admin/adicionar_colaborador_manual.html', cargos=cargos, departamentos=departamentos, superiores=superiores)


@colaborador_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar(id):
    colaborador = Colaborador.query.get_or_404(id)
    if request.method == 'POST':
        novo_superior_id = request.form.get('superior_id')
        novo_superior_id = int(
            novo_superior_id) if novo_superior_id and novo_superior_id != 'None' else None

        if is_circular_reference(id, novo_superior_id):
            flash('Erro de hierarquia: Um colaborador não pode ser seu próprio superior, nem ser superior de alguém que já está acima dele.', 'danger')
            return redirect(url_for('colaborador.editar', id=id))

        colaborador.nome = request.form.get('nome')
        colaborador.sobrenome = request.form.get('sobrenome')
        colaborador.email_corporativo = request.form.get('email_corporativo')
        colaborador.data_nascimento = pd.to_datetime(
            request.form.get('data_nascimento'), dayfirst=True).date()
        colaborador.data_inicio = pd.to_datetime(
            request.form.get('data_inicio'), dayfirst=True).date()
        colaborador.cargo_id = int(request.form.get(
            'cargo_id')) if request.form.get('cargo_id') else None
        colaborador.departamento_id = int(request.form.get(
            'departamento_id')) if request.form.get('departamento_id') else None
        colaborador.superior_id = novo_superior_id

        if 'foto' in request.files and request.files['foto'].filename != '':
            colaborador.foto_filename = salvar_foto(request.files['foto'])

        nova_senha = request.form.get('senha')
        if nova_senha:
            colaborador.set_password(nova_senha)

        db.session.commit()
        flash('Colaborador atualizado com sucesso!', 'success')
        return redirect(url_for('colaborador.listar'))

    cargos = Cargo.query.order_by(Cargo.titulo).all()
    departamentos = Departamento.query.order_by(Departamento.nome).all()
    superiores = Colaborador.query.filter(
        Colaborador.id != id).order_by(Colaborador.nome).all()
    return render_template('admin/edit_colaborador.html', colaborador=colaborador, cargos=cargos, departamentos=departamentos, superiores=superiores)


@colaborador_bp.route('/remover/<int:id>', methods=['POST'])
@admin_required
def remover(id):
    colaborador = Colaborador.query.get_or_404(id)
    nome_completo = f"{colaborador.nome} {colaborador.sobrenome}"
    db.session.delete(colaborador)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Colaborador {nome_completo} removido com sucesso!'})


@colaborador_bp.route('/importar', methods=['GET', 'POST'])
@admin_required
def importar():
    if request.method == 'POST':
        if 'planilha_colaboradores' not in request.files:
            flash('Nenhum ficheiro selecionado.', 'warning')
            return redirect(request.url)

        file = request.files['planilha_colaboradores']
        if file.filename == '':
            flash('Nenhum ficheiro selecionado.', 'warning')
            return redirect(request.url)

        if file and file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file, engine='openpyxl')
                novos_colaboradores = 0
                erros = []

                for index, row in df.iterrows():
                    email = row.get('email_corporativo')
                    if not email or Colaborador.query.filter_by(email_corporativo=email).first():
                        erros.append(
                            f"Linha {index+2}: E-mail '{email}' já existe ou está em branco.")
                        continue

                    novo_colaborador = Colaborador(
                        nome=row.get('nome'),
                        sobrenome=row.get('sobrenome'),
                        email_corporativo=email,
                        data_nascimento=pd.to_datetime(
                            row.get('data_nascimento')).date(),
                        data_inicio=pd.to_datetime(
                            row.get('data_inicio')).date()
                    )
                    novo_colaborador.set_password(str(row.get('senha')))
                    db.session.add(novo_colaborador)
                    novos_colaboradores += 1

                db.session.commit()

                if novos_colaboradores > 0:
                    flash(
                        f'{novos_colaboradores} colaborador(es) importado(s) com sucesso!', 'success')
                if erros:
                    flash('Alguns registos não foram importados:', 'danger')
                    for erro in erros:
                        flash(erro, 'danger')

            except Exception as e:
                db.session.rollback()
                flash(
                    f'Ocorreu um erro ao processar o ficheiro: {e}', 'danger')

            return redirect(url_for('colaborador.listar'))

    return render_template('admin/importar_colaboradores.html')


@colaborador_bp.route('/baixar_modelo')
@admin_required
def baixar_modelo():
    colunas = ['nome', 'sobrenome', 'email_corporativo',
               'data_nascimento', 'data_inicio', 'senha']
    df_modelo = pd.DataFrame(columns=colunas)
    buffer = io.BytesIO()
    df_modelo.to_excel(buffer, index=False,
                       sheet_name='colaboradores', engine='openpyxl')
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='modelo_importacao.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


def is_circular_reference(colaborador_id, novo_superior_id):
    if not novo_superior_id or not colaborador_id:
        return False
    if int(colaborador_id) == int(novo_superior_id):
        return True
    visitados = set()
    atual = Colaborador.query.get(novo_superior_id)
    while atual:
        if atual.id in visitados:
            break
        visitados.add(atual.id)
        if atual.superior_id == int(colaborador_id):
            return True
        atual = atual.superior
    return False
