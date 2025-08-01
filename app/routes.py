from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import extract, desc
from . import db
from .models import Aviso, Colaborador, Destaque, FaqCategoria, FaqPergunta, Ouvidoria, Evento, ConfigLink, Cargo
import locale

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

    aniversariantes_empresa = Colaborador.query.filter(
        extract('month', Colaborador.data_inicio) == hoje.month,
        Colaborador.data_inicio.isnot(None)
    ).order_by(extract('day', Colaborador.data_inicio)).all()

    for aniv in aniversariantes_empresa:
        anos_de_casa = hoje.year - aniv.data_inicio.year
        if (hoje.month, hoje.day) < (aniv.data_inicio.month, aniv.data_inicio.day):
            anos_de_casa -= 1
        aniv.anos_de_casa = anos_de_casa if anos_de_casa > 0 else 1

    primeiro_dia_do_mes_atual = hoje.replace(day=1)
    ultimo_dia_do_mes_anterior = primeiro_dia_do_mes_atual - timedelta(days=1)

    ano_destaque = ultimo_dia_do_mes_anterior.year
    mes_destaque = ultimo_dia_do_mes_anterior.month

    nome_mes_destaque = ultimo_dia_do_mes_anterior.strftime('%B').capitalize()

    destaques_do_mes = Destaque.query.filter_by(
        ano=ano_destaque, mes=mes_destaque).all()

    eventos_proximos_obj = Evento.query.filter(
        Evento.start >= hoje
    ).order_by(Evento.start.asc()).limit(5).all()
    eventos_proximos_dict = [evento.to_dict()
                             for evento in eventos_proximos_obj]

    link_vagas_obj = ConfigLink.query.filter_by(chave='link_vagas').first()
    link_indicacao_obj = ConfigLink.query.filter_by(
        chave='link_indicacao').first()
    links_carreira = {
        'vagas': link_vagas_obj.valor if link_vagas_obj else None,
        'indicacao': link_indicacao_obj.valor if link_indicacao_obj else None
    }

    return render_template(
        'index.html',
        total_colaboradores=total_colaboradores,
        avisos=avisos_dict,
        aniversariantes=aniversariantes_do_mes,
        destaques=destaques_do_mes,
        nome_mes_destaque=nome_mes_destaque,
        aniversariantes_empresa=aniversariantes_empresa,
        eventos=eventos_proximos_dict,
        links_carreira=links_carreira,
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


@main.route('/organograma')
@login_required
def ver_organograma():
    """ Rota que renderiza a página de visualização do organograma. """
    return render_template('organograma.html', title="Organograma Corporativo")


def get_equipe_recursive(colaborador_id, todos_colaboradores):
    """ Função auxiliar para encontrar todos os subordinados de um colaborador """
    equipe = []
    subordinados_diretos = [c for c in todos_colaboradores if c.superior_id == colaborador_id]

    for sub in subordinados_diretos:
        equipe.append(sub)
        equipe.extend(get_equipe_recursive(sub.id, todos_colaboradores))

    return equipe


@main.route('/api/organograma-data')
@login_required
def organograma_data():
    """ 
    Endpoint que retorna os dados dos colaboradores no formato JSON
    a partir de um único CEO definido.
    """
    config_ceo = ConfigLink.query.filter_by(chave='ceo_colaborador_id').first()
    if not config_ceo or not config_ceo.valor:
        # Se nenhum CEO estiver definido, retorna uma lista vazia para não dar erro
        return jsonify({'nodes': []})

    ceo_id = int(config_ceo.valor)
    ceo = Colaborador.query.get(ceo_id)
    if not ceo:
        return jsonify({'nodes': []})

    # Pega todos os colaboradores de uma vez para evitar múltiplas queries
    todos_colaboradores = Colaborador.query.all()

    # Monta a árvore hierárquica a partir do CEO
    arvore_colaboradores = [ceo] + get_equipe_recursive(ceo_id, todos_colaboradores)

    nodes = []
    for col in arvore_colaboradores:
        # Garante que o CEO não tenha um pai, resolvendo o erro 'multiple roots'
        parent_id = col.superior_id if col.id != ceo_id else None

        nodes.append({
            'id': col.id,
            'parentId': parent_id,
            'nome': f"{col.nome} {col.sobrenome}",
            'cargo': col.cargo.titulo if col.cargo else 'Sem Cargo',
            'departamento': col.departamento.nome if col.departamento else 'N/A',
            'imageUrl': f"/static/fotos_colaboradores/{col.foto_filename}" if col.foto_filename else "/static/img/default_avatar.png",
        })
    return jsonify({'nodes': nodes})
