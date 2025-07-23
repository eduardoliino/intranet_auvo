# app/routes.py

from flask import Blueprint, render_template
from app.models import Aviso, Colaborador  # Importe os dois modelos aqui

# 1. Cria o Blueprint. 'main' é o nome que daremos a este conjunto de rotas.
main = Blueprint('main', __name__)

# 2. Agora os decoradores de rota usam o Blueprint ('main'), não mais o 'app'.


@main.route('/')
@main.route('/index')
def index():
    # --- BUSCANDO DADOS REAIS DO BANCO DE DADOS ---
    aviso_recente = Aviso.query.order_by(Aviso.id.desc()).first()
    total_colaboradores = Colaborador.query.count()

    # --- DADOS QUE AINDA SÃO FALSOS (até criarmos os modelos para eles) ---
    aniversariantes = ["Carlos (Setor Vendas)", "Juliana (Setor Suporte)"]
    destaques_comercial = "Equipe Alfa por atingir 125% da meta."

    # --- ENVIANDO TUDO PARA O TEMPLATE ---
    return render_template(
        'index.html',
        title='Início',
        # Variáveis com dados reais:
        aviso=aviso_recente,
        total_colaboradores=total_colaboradores,
        # Variáveis com dados falsos (temporário):
        aniversariantes=aniversariantes,
        destaque_comercial=destaques_comercial
    )
