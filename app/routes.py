from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import extract, desc
from . import db
from .models import Aviso, Colaborador, Destaque, FaqCategoria, FaqPergunta, Ouvidoria, Evento
import locale  # Importe a biblioteca de localização

# Defina a localização para português do Brasil para obter nomes de meses corretos
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
@login_required
def index():
    total_colaboradores = Colaborador.query.count()
    avisos_obj = Aviso.query.order_by(
        Aviso.data_criacao.desc()).limit(10).all()
    avisos_dict = [aviso.to_dict() for aviso in avisos_obj]

    hoje = datetime.utcnow()
    aniversariantes_do_mes = Colaborador.query.filter(
        extract('month', Colaborador.data_nascimento) == hoje.month
    ).order_by(extract('day', Colaborador.data_nascimento)).all()

    # --- ÁREA DA ALTERAÇÃO: Lógica para buscar destaques do mês anterior ---
    primeiro_dia_do_mes_atual = hoje.replace(day=1)
    ultimo_dia_do_mes_anterior = primeiro_dia_do_mes_atual - timedelta(days=1)

    ano_destaque = ultimo_dia_do_mes_anterior.year
    mes_destaque = ultimo_dia_do_mes_anterior.month

    # Obtém o nome do mês em português (Ex: "Julho")
    nome_mes_destaque = ultimo_dia_do_mes_anterior.strftime('%B').capitalize()

    destaques_do_mes = Destaque.query.filter_by(
        ano=ano_destaque, mes=mes_destaque).all()
    # --- FIM DA ÁREA DA ALTERAÇÃO ---

    eventos_proximos_obj = Evento.query.filter(
        Evento.start >= hoje
    ).order_by(Evento.start.asc()).limit(5).all()
    eventos_proximos_dict = [evento.to_dict()
                             for evento in eventos_proximos_obj]

    return render_template(
        'index.html',
        total_colaboradores=total_colaboradores,
        avisos=avisos_dict,
        aniversariantes=aniversariantes_do_mes,
        destaques=destaques_do_mes,
        nome_mes_destaque=nome_mes_destaque,  # Passa o nome do mês para o template
        eventos=eventos_proximos_dict,
        current_user=current_user
    )


@main.route('/aviso/<int:aviso_id>')
@login_required
def aviso_detalhe(aviso_id):
    aviso = Aviso.query.get_or_404(aviso_id)
    return render_template('aviso_detalhe.html', title=aviso.titulo, aviso=aviso)


@main.route('/faq')
@login_required
def faq_publico():
    total_colaboradores = Colaborador.query.count()
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
    return render_template(
        'faq.html',
        title='FAQ',
        categorias=categorias_json,
        perguntas=perguntas_json,
        total_colaboradores=total_colaboradores
    )


@main.route('/ouvidoria', methods=['GET', 'POST'])
@login_required
def ouvidoria():
    total_colaboradores = Colaborador.query.count()

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
    return render_template(
        'ouvidoria.html',
        title='Ouvidoria',
        total_colaboradores=total_colaboradores
    )
