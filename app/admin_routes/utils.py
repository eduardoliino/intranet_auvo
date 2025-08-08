import os
import secrets
from functools import wraps
from flask import flash, redirect, url_for, current_app
from flask_login import current_user


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
    foto_path = os.path.join(
        current_app.root_path, 'static/fotos_colaboradores', foto_filename
    )
    os.makedirs(os.path.dirname(foto_path), exist_ok=True)
    form_foto.save(foto_path)
    return foto_filename
