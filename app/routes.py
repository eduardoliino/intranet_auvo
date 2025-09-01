from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import extract, desc, or_
from . import db
from .models import Aviso, Colaborador, Destaque, FaqCategoria, FaqPergunta, Ouvidoria, Evento, ConfigLink, Cargo
from app.newsletter.models import NewsPost
import locale
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    pass

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
@login_required
def index():
    """Renderiza a página inicial com avisos e destaques."""
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

    # Post mais recente da Newsletter (publicado)
    latest_post = NewsPost.query.filter_by(status='publicado').order_by(NewsPost.publicado_em.desc()).first()

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
        latest_post=latest_post,
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
    categorias_obj = FaqCategoria.query.order_by(FaqCategoria.nome).all()
    categorias_json = [{'id': cat.id, 'nome': cat.nome}
                       for cat in categorias_obj]
    return render_template(
        'faq.html',
        title='FAQ',
        categorias=categorias_json
    )


@main.route('/api/faq')
@login_required
def api_faq_data():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '', type=str)
    category_id = request.args.get('category', None, type=int)

    query = FaqPergunta.query.order_by(FaqPergunta.id.desc())

    if category_id:
        query = query.filter(FaqPergunta.categoria_id == category_id)

    if search_term:
        search_filter = f"%{search_term}%"
        query = query.filter(
            or_(
                FaqPergunta.pergunta.ilike(search_filter),
                FaqPergunta.resposta.ilike(search_filter),
                FaqPergunta.palavras_chave.ilike(search_filter)
            )
        )

    paginated_perguntas = query.paginate(
        page=page, per_page=15, error_out=False)

    return jsonify({
        'perguntas': [p.to_dict() for p in paginated_perguntas.items],
        'has_next': paginated_perguntas.has_next
    })


@main.route('/api/ouvidoria/status')
@login_required
def api_ouvidoria_status():
    if not current_user.tem_permissao('gerenciar_ouvidoria'):
        return jsonify({'has_new': False}), 403

    tem_nova = db.session.query(
        Ouvidoria.query.filter_by(status='Nova').exists()).scalar()
    return jsonify({'has_new': tem_nova})


@main.route('/ouvidoria', methods=['GET', 'POST'])
@login_required
def ouvidoria():
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


@main.route('/organograma')
@login_required
def ver_organograma():
    return render_template('organograma.html', title="Organograma Corporativo")


def get_equipe_recursive(colaborador_id, todos_colaboradores, visitados):
    """Retorna recursivamente a equipa subordinada a um colaborador."""
    if colaborador_id in visitados:
        return []
    visitados.add(colaborador_id)
    equipe = []
    subordinados_diretos = [
        c for c in todos_colaboradores
        if c.superior_id == colaborador_id and c.id != c.superior_id
    ]
    for sub in subordinados_diretos:
        equipe.append(sub)
        equipe.extend(get_equipe_recursive(
            sub.id, todos_colaboradores, visitados))
    return equipe


@main.route('/api/organograma-data')
@login_required
def organograma_data():
    """Monta os dados do organograma corporativo em formato JSON."""
    config_ceo = ConfigLink.query.filter_by(chave='ceo_colaborador_id').first()
    if not config_ceo or not config_ceo.valor:
        return jsonify({'nodes': []})

    ceo_id = int(config_ceo.valor)
    ceo = Colaborador.query.get(ceo_id)
    if not ceo:
        return jsonify({'nodes': []})

    todos_colaboradores = Colaborador.query.all()
    arvore_colaboradores = [
        ceo] + get_equipe_recursive(ceo_id, todos_colaboradores, set())

    nodes_dict = {}
    for col in arvore_colaboradores:
        if col.id not in nodes_dict:
            parent_id = col.superior_id if col.id != ceo_id else None
            if col.id == col.superior_id:
                parent_id = None

            nodes_dict[col.id] = {
                'id': col.id,
                'parentId': parent_id,
                'nome': f"{col.nome} {col.sobrenome}",
                'cargo': col.cargo.titulo if col.cargo else 'Sem Cargo',
                'departamento': col.departamento.nome if col.departamento else 'N/A',
                'imageUrl': f"/static/fotos_colaboradores/{col.foto_filename}" if col.foto_filename else "/static/img/default_avatar.png",
            }

    nodes = list(nodes_dict.values())
    return jsonify({'nodes': nodes})


@main.route('/api/colaborador/<int:id>')
@login_required
def get_colaborador_detalhes(id):
    col = Colaborador.query.get_or_404(id)
    return jsonify({
        'id': col.id,
        'nome_completo': f"{col.nome} {col.sobrenome}",
        'email': col.email_corporativo,
        'cargo': col.cargo.titulo if col.cargo else "N/A",
        'departamento': col.departamento.nome if col.departamento else "N/A",
        'foto_url': f"/static/fotos_colaboradores/{col.foto_filename}" if col.foto_filename else "/static/img/default_avatar.png"
    })
