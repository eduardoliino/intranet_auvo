# app/routes.py

from flask import Blueprint, render_template

# 1. Cria o Blueprint. 'main' é o nome que daremos a este conjunto de rotas.
main = Blueprint('main', __name__)

# 2. Agora os decoradores de rota usam o Blueprint ('main'), não mais o 'app'.


@main.route('/')
@main.route('/index')
def index():
    # Passamos os dados falsos aqui por enquanto, para os cards.
    avisos_rh = "Feriado de Corpus Christi será na próxima quinta-feira. Não haverá expediente."
    aniversariantes = ["Carlos (Setor Vendas)", "Juliana (Setor Suporte)"]
    destaques_comercial = "Equipe Alfa por atingir 125% da meta."
    contador_colaboradores = 152

    return render_template(
        'index.html',
        title='Início',
        avisos=avisos_rh,
        aniversariantes=aniversariantes,
        destaque_comercial=destaques_comercial,
        total_colaboradores=contador_colaboradores
    )
