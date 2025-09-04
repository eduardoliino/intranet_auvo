from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from .models import Colaborador

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Processa o login dos colaboradores."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        identifier = request.form.get('email')
        password = request.form.get('password')

        colaborador_user = Colaborador.query.filter_by(
            email_corporativo=identifier).first()
        if colaborador_user and colaborador_user.check_password(password):
            login_user(colaborador_user, remember=False)
            return redirect(url_for('main.index'))

        flash('Email ou senha inválidos. Por favor, tente novamente.', 'danger')
        return render_template('login.html', email=identifier)

    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    """Encerra a sessão do utilizador e limpa os dados temporários."""
    logout_user()

    session.clear()

    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))
