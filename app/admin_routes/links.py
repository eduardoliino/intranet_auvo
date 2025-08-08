from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import db
from app.models import ConfigLink
from . import admin
from .utils import admin_required


@admin.route('/links', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_links():
    if request.method == 'POST':
        link_vagas_url = request.form.get('link_vagas')
        link_indicacao_url = request.form.get('link_indicacao')

        def upsert_link(chave, valor):
            link = ConfigLink.query.filter_by(chave=chave).first()
            if link:
                link.valor = valor
            else:
                link = ConfigLink(chave=chave, valor=valor)
                db.session.add(link)

        upsert_link('link_vagas', link_vagas_url)
        upsert_link('link_indicacao', link_indicacao_url)

        db.session.commit()
        flash('Links atualizados com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_links'))

    link_vagas = ConfigLink.query.filter_by(chave='link_vagas').first()
    link_indicacao = ConfigLink.query.filter_by(chave='link_indicacao').first()

    links = {
        'vagas': link_vagas.valor if link_vagas else '',
        'indicacao': link_indicacao.valor if link_indicacao else '',
    }

    return render_template('admin/gerenciar_links.html', links=links)
