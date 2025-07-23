# app/admin_routes.py

import pandas as pd
from flask import Blueprint, render_template, request, flash, redirect, url_for
# 1. Importe o login_required aqui
from flask_login import login_required
from app import db
from app.models import Colaborador

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Rota para listar todos os colaboradores


@admin.route('/colaboradores')
@login_required  # 2. Ative o decorador aqui
def listar_colaboradores():
    colaboradores = Colaborador.query.all()
    total = len(colaboradores)
    return render_template('admin/listar_colaboradores.html', colaboradores=colaboradores, total=total)

# Rota para adicionar, editar e importar


@admin.route('/colaboradores/gerenciar', methods=['GET', 'POST'])
@login_required  # 3. E ative aqui também
def gerenciar_colaboradores():
    if request.method == 'POST':
        # Lógica para importar planilha
        if 'planilha_colaboradores' in request.files:
            arquivo = request.files['planilha_colaboradores']
            if arquivo.filename != '' and arquivo.filename.endswith('.xlsx'):
                try:
                    df = pd.read_excel(arquivo)
                    # Verifique se as colunas esperadas existem
                    colunas_necessarias = [
                        'nome', 'sobrenome', 'email_corporativo', 'data_nascimento', 'senha']
                    if not all(coluna in df.columns for coluna in colunas_necessarias):
                        flash(
                            'A planilha não contém todas as colunas necessárias.', 'danger')
                        return redirect(url_for('admin.gerenciar_colaboradores'))

                    for index, row in df.iterrows():
                        # Evita adicionar e-mails duplicados
                        if not Colaborador.query.filter_by(email_corporativo=row['email_corporativo']).first():
                            novo_colaborador = Colaborador(
                                nome=row['nome'],
                                sobrenome=row['sobrenome'],
                                email_corporativo=row['email_corporativo'],
                                data_nascimento=pd.to_datetime(
                                    row['data_nascimento']).date()
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

    return render_template('admin/gerenciar_colaboradores.html')
