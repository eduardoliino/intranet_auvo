from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import extract, desc
from . import db
from .models import Aviso, Colaborador, Destaque, FaqCategoria, FaqPergunta, Ouvidoria, Evento

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
@login_required
def index():
    # --- BUSCANDO DADOS PARA O DASHBOARD ---
    total_colaboradores = Colaborador.query.count()

    # 1. Avisos: Busca os 10 mais recentes, ordenados pela data de criação
    # (É necessário adicionar a coluna 'data_criacao' no modelo 'Aviso')
    avisos_obj = Aviso.query.order_by(
        Aviso.data_criacao.desc()).limit(10).all()
    # --- NOVA LINHA PARA CONVERTER OS OBJETOS ---
    avisos_dict = [aviso.to_dict() for aviso in avisos_obj]

    # 2. Aniversariantes: Busca TODOS os aniversariantes do mês atual
    hoje = datetime.utcnow()
    aniversariantes_do_mes = Colaborador.query.filter(
        extract('month', Colaborador.data_nascimento) == hoje.month
    ).order_by(extract('day', Colaborador.data_nascimento)).all()

    # 3. Destaques: Busca todos os destaques do mês e ano atuais
    destaques_do_mes = Destaque.query.filter_by(
        ano=hoje.year, mes=hoje.month).all()

    # 4. Eventos: Busca os 5 próximos eventos a partir de hoje
    eventos_proximos = Evento.query.filter(
        Evento.start >= hoje
    ).order_by(Evento.start.asc()).limit(5).all()

    return render_template(
        'index.html',  # <-- Mude esta linha!
        total_colaboradores=total_colaboradores,
        avisos=avisos_dict,  # <-- Passe a lista de dicionários, não de objetos
        # <-- Corrigido para enviar todos do mês
        aniversariantes=aniversariantes_do_mes,
        destaques=destaques_do_mes,
        eventos=eventos_proximos,  # <-- Enviando os objetos diretamente
        current_user=current_user  # Garante que current_user está disponível no template
    )

# --- Rota para exibir um aviso completo ---


@main.route('/aviso/<int:aviso_id>')
@login_required  # <-- Adicione esta proteção
def aviso_detalhe(aviso_id):
    aviso = Aviso.query.get_or_404(aviso_id)
    return render_template('aviso_detalhe.html', title=aviso.titulo, aviso=aviso)


@main.route('/faq')
@login_required  # <-- Adicione esta proteção
def faq_publico():
    # ... (o seu código do FAQ permanece igual)
    categorias_obj = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    perguntas_obj = FaqPergunta.query.order_by(FaqPergunta.id.desc()).all()
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
    return render_template('faq.html', title='FAQ', categorias=categorias_json, perguntas=perguntas_json)


@main.route('/ouvidoria', methods=['GET', 'POST'])
@login_required  # <-- Adicione esta proteção
def ouvidoria():
    # ... (o seu código da Ouvidoria permanece igual)
    if request.method == 'POST':
        tipo_denuncia = request.form.get('tipo_denuncia')
        mensagem = request.form.get('mensagem')
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
        return jsonify({
            'success': True,
            'message': 'A sua mensagem foi enviada com sucesso! Agradecemos a sua contribuição.'
        })
    return render_template('ouvidoria.html', title='Ouvidoria')
