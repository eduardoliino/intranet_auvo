# app/colaborador_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app
from flask_login import login_required
from app import db
from app.models import Colaborador, Cargo, Departamento
from app.admin_routes import admin_required, salvar_foto
import pandas as pd
import io
import os

colaborador_bp = Blueprint('colaborador', __name__,
                           url_prefix='/admin/colaboradores')


@colaborador_bp.route('/')
@admin_required
def listar():
    colaboradores_objetos = Colaborador.query.order_by(Colaborador.nome).all()
    # --- CORREÇÃO APLICADA AQUI ---
    # Converte a lista de objetos para uma lista de dicionários
    colaboradores_json = [
        {
            'id': c.id,
            'nome': c.nome,
            'sobrenome': c.sobrenome,
            'email_corporativo': c.email_corporativo,
            'foto_filename': c.foto_filename
        }
        for c in colaboradores_objetos
    ]
    return render_template('admin/listar_colaboradores.html', colaboradores=colaboradores_json)


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
                request.form.get('data_nascimento')).date(),
            data_inicio=pd.to_datetime(request.form.get('data_inicio')).date(),
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

    # Para o método GET
    cargos = Cargo.query.order_by(Cargo.titulo).all()
    departamentos = Departamento.query.order_by(Departamento.nome).all()
    superiores = Colaborador.query.order_by(Colaborador.nome).all()
    return render_template('admin/adicionar_colaborador_manual.html', cargos=cargos, departamentos=departamentos, superiores=superiores)


@colaborador_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar(id):
    colaborador = Colaborador.query.get_or_404(id)
    if request.method == 'POST':
        # Atualização dos dados...
        colaborador.nome = request.form.get('nome')
        colaborador.sobrenome = request.form.get('sobrenome')
        colaborador.email_corporativo = request.form.get('email_corporativo')
        colaborador.data_nascimento = pd.to_datetime(
            request.form.get('data_nascimento')).date()
        colaborador.data_inicio = pd.to_datetime(
            request.form.get('data_inicio')).date()

        colaborador.cargo_id = int(request.form.get(
            'cargo_id')) if request.form.get('cargo_id') else None
        colaborador.departamento_id = int(request.form.get(
            'departamento_id')) if request.form.get('departamento_id') else None
        colaborador.superior_id = int(request.form.get(
            'superior_id')) if request.form.get('superior_id') != 'None' else None

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


@colaborador_bp.route('/remover/<int:id>')
@admin_required
def remover(id):
    colaborador = Colaborador.query.get_or_404(id)
    db.session.delete(colaborador)
    db.session.commit()
    flash('Colaborador removido com sucesso!', 'success')
    return redirect(url_for('colaborador.listar'))

# --- Rotas de Importação ---


@colaborador_bp.route('/importar', methods=['GET', 'POST'])
@admin_required
def importar():
    if request.method == 'POST':
        if 'planilha_colaboradores' not in request.files:
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(url_for('colaborador.importar'))
        arquivo = request.files['planilha_colaboradores']
        if arquivo.filename == '' or not arquivo.filename.endswith('.xlsx'):
            flash('Arquivo inválido. Por favor, envie um arquivo .xlsx.', 'danger')
            return redirect(url_for('colaborador.importar'))
        try:
            df = pd.read_excel(arquivo)
            colunas_necessarias = [
                'nome', 'sobrenome', 'email_corporativo', 'data_nascimento', 'data_inicio', 'senha']
            if not all(coluna in df.columns for coluna in colunas_necessarias):
                flash('A planilha não contém todas as colunas necessárias.', 'danger')
                return redirect(url_for('colaborador.importar'))
            for index, row in df.iterrows():
                if Colaborador.query.filter_by(email_corporativo=row['email_corporativo']).first():
                    continue
                novo_colaborador = Colaborador(
                    nome=row['nome'], sobrenome=row['sobrenome'],
                    email_corporativo=row['email_corporativo'],
                    data_nascimento=pd.to_datetime(
                        row['data_nascimento']).date(),
                    data_inicio=pd.to_datetime(row['data_inicio']).date()
                )
                novo_colaborador.set_password(str(row['senha']))
                db.session.add(novo_colaborador)
            db.session.commit()
            flash('Colaboradores importados com sucesso! Cargo e departamento devem ser definidos manualmente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao importar: {e}', 'danger')
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
