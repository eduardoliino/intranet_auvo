# app/routes.py

from flask import Blueprint, render_template
from datetime import datetime, timedelta
from sqlalchemy import extract
from .models import Aviso, Colaborador, Destaque  # Adicione Destaque aqui

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
def index():
    # --- Dados para os cards ---
    aviso_recente = Aviso.query.order_by(Aviso.id.desc()).first()
    total_colaboradores = Colaborador.query.count()

    # --- Lógica para Aniversariantes do Mês ---
    mes_atual = datetime.utcnow().month
    aniversariantes_do_mes = Colaborador.query.filter(
        extract('month', Colaborador.data_nascimento) == mes_atual
    ).order_by(extract('day', Colaborador.data_nascimento)).all()

    # --- LÓGICA PARA BUSCAR DESTAQUES RECENTES ---
    hoje = datetime.utcnow()
    # Pega destaques dos últimos ~3 meses
    limite_data = hoje - timedelta(days=90)
    destaques_recentes = Destaque.query.filter(
        Destaque.ano >= limite_data.year,
        Destaque.mes >= limite_data.month
    ).order_by(Destaque.ano.desc(), Destaque.mes.desc()).all()
    # --------------------------------------------

    return render_template(
        'index.html',
        title='Início',
        aviso=aviso_recente,
        total_colaboradores=total_colaboradores,
        aniversariantes=aniversariantes_do_mes,
        # Envia a lista real de destaques para o template
        destaques=destaques_recentes
    )

# --- Rota para exibir um aviso completo ---


@main.route('/aviso/<int:aviso_id>')
def aviso_detalhe(aviso_id):
    aviso = Aviso.query.get_or_404(aviso_id)
    return render_template('aviso_detalhe.html', title=aviso.titulo, aviso=aviso)
