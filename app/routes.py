# app/routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from datetime import datetime, timedelta
from sqlalchemy import extract
# Adicione 'db' aqui para que a rota da ouvidoria funcione
from . import db
from .models import Aviso, Colaborador, Destaque, FaqCategoria, FaqPergunta, Ouvidoria

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


@main.route('/faq')
def faq_publico():
    # Busca os objetos da base de dados
    categorias_obj = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    perguntas_obj = FaqPergunta.query.order_by(FaqPergunta.id.desc()).all()

    # --- CORREÇÃO: Converte os objetos para listas de dicionários ---
    categorias_json = [{'id': cat.id, 'nome': cat.nome}
                       for cat in categorias_obj]
    perguntas_json = [{
        'id': p.id,
        'pergunta': p.pergunta,
        'resposta': p.resposta,
        'palavras_chave': p.palavras_chave,
        'link_url': p.link_url,
        'link_texto': p.link_texto,
        'categoria_id': p.categoria_id
    } for p in perguntas_obj]
    # ----------------------------------------------------------------

    # Envia as listas de dicionários (agora compatíveis com JSON) para o template
    return render_template('faq.html', title='FAQ', categorias=categorias_json, perguntas=perguntas_json)


@main.route('/ouvidoria', methods=['GET', 'POST'])
def ouvidoria():
    if request.method == 'POST':
        tipo_denuncia = request.form.get('tipo_denuncia')
        mensagem = request.form.get('mensagem')
        # A forma como o formulário envia o 'checkbox' pode variar, vamos tratar os casos
        identificado_str = request.form.get('identificado', 'false')
        identificado = identificado_str.lower() in ['true', 'on']

        nome = request.form.get('nome') if identificado else None
        contato = request.form.get('contato') if identificado else None

        if not tipo_denuncia or not mensagem:
            return jsonify({'success': False, 'message': 'Assunto e Mensagem são obrigatórios.'}), 400

        nova_entrada = Ouvidoria(
            tipo_denuncia=tipo_denuncia,
            mensagem=mensagem,
            anonima=(not identificado),
            nome=nome,
            contato=contato
        )
        db.session.add(nova_entrada)
        db.session.commit()

        # Em vez de redirecionar, devolve uma resposta de sucesso em JSON
        return jsonify({
            'success': True,
            'message': 'A sua mensagem foi enviada com sucesso! Agradecemos a sua contribuição.'
        })

    return render_template('ouvidoria.html', title='Ouvidoria')
