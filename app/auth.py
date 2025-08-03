from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Colaborador

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Se o utilizador já estiver logado, vai direto para a dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # O campo 'email' do formulário será usado para ambos os tipos de login
        identifier = request.form.get('email')
        password = request.form.get('password')

        # 1. Primeiro, verifica se as credenciais são de um administrador (User)
        admin_user = User.query.filter_by(username=identifier).first()
        if admin_user and admin_user.check_password(password):
            login_user(admin_user)
            # Se for admin, redireciona para uma página de gestão
            return redirect(url_for('colaborador.listar'))

        # 2. Se não for admin, verifica se as credenciais são de um colaborador
        colaborador_user = Colaborador.query.filter_by(
            email_corporativo=identifier).first()
        if colaborador_user and colaborador_user.check_password(password):
            login_user(colaborador_user)
            # Se for colaborador, redireciona para a dashboard principal
            return redirect(url_for('main.index'))

        # 3. Se não for nenhum dos dois, mostra uma mensagem de erro
        flash('Utilizador ou senha inválidos. Por favor, tente novamente.', 'danger')
        return redirect(url_for('auth.login'))

    # Usa a nova e bonita tela de login para todos
    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    # Após o logout, redireciona sempre para a nova tela de login unificada
    return redirect(url_for('auth.login'))
