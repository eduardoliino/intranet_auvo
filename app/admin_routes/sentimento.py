from flask import render_template, request
from flask_login import login_required
from datetime import datetime, timedelta, timezone

from app import db
from . import admin
from .utils import admin_required
from app.models import Colaborador, SentimentoDia


def _today_local():
    tz = timezone(timedelta(hours=-3))
    return datetime.now(tz).date()

@admin.route('/sentimento')
@login_required
@admin_required
def admin_sentimento():
    today = _today_local()
    total_colabs = Colaborador.query.count()

    # Filtros opcionais (modo detalhado)
    user_id = request.args.get('user_id', type=int)
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    # Parse datas (YYYY-MM-DD); padrão últimos 30 dias
    def parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except Exception:
            return None

    start = parse_date(start_str) if start_str else None
    end = parse_date(end_str) if end_str else None
    if not start or not end:
        end = today
        start = end - timedelta(days=30)

    colaboradores = Colaborador.query.order_by(Colaborador.nome).all()

    detailed = None
    if user_id:
        # Consulta detalhada do colaborador no período
        qs = SentimentoDia.query \
            .filter(SentimentoDia.usuario_id == user_id) \
            .filter(SentimentoDia.data >= start, SentimentoDia.data <= end) \
            .order_by(SentimentoDia.data.asc())
        registros = qs.all()
        dist_user = {'muito_triste': 0, 'triste': 0, 'neutro': 0, 'feliz': 0, 'muito_feliz': 0}
        for r in registros:
            dist_user[r.sentimento] = dist_user.get(r.sentimento, 0) + 1

        dias_periodo = (end - start).days + 1
        dias_respondidos = len(registros)
        # média “numérica” do humor (opcional para análise):
        map_val = {'muito_triste': 1, 'triste': 2, 'neutro': 3, 'feliz': 4, 'muito_feliz': 5}
        media_val = round(sum(map_val[r.sentimento] for r in registros)/dias_respondidos, 2) if dias_respondidos else None

        # maior sequência de tristeza no período (não dispara alerta, apenas métrica)
        max_streak = 0
        current_streak = 0
        prev_date = None
        for r in registros:
            if r.sentimento in ('triste', 'muito_triste'):
                if prev_date and (r.data - prev_date == timedelta(days=1)):
                    current_streak += 1
                else:
                    current_streak = 1
            else:
                current_streak = 0
            max_streak = max(max_streak, current_streak)
            prev_date = r.data

        detailed = {
            'user_id': user_id,
            'start': start,
            'end': end,
            'registros': registros,
            'dist': dist_user,
            'dias_periodo': dias_periodo,
            'dias_respondidos': dias_respondidos,
            'percent_participacao': round((dias_respondidos/dias_periodo)*100, 1) if dias_periodo else 0,
            'media_humor': media_val,
            'max_streak_triste': max_streak,
        }

    # Resumo do dia (sempre mostrado)
    hoje = SentimentoDia.query.filter_by(data=today).all()
    dist = {'muito_triste': 0, 'triste': 0, 'neutro': 0, 'feliz': 0, 'muito_feliz': 0}
    for r in hoje:
        dist[r.sentimento] = dist.get(r.sentimento, 0) + 1
    participantes = len(hoje)

    # Alertas (14 dias, 3+ dias consecutivos) – permanece igual
    lookback_days = 14
    al_start = today - timedelta(days=lookback_days)
    sentimentos_periodo = SentimentoDia.query \
        .filter(SentimentoDia.data >= al_start) \
        .order_by(SentimentoDia.usuario_id, SentimentoDia.data.desc()).all()

    seq_por_usuario = {}
    for rec in sentimentos_periodo:
        if rec.usuario_id not in seq_por_usuario:
            seq_por_usuario[rec.usuario_id] = 0
        if rec.sentimento in ('triste', 'muito_triste'):
            key = f"last_{rec.usuario_id}"
            if key not in seq_por_usuario:
                seq_por_usuario[key] = rec.data
                seq_por_usuario[rec.usuario_id] = 1
            else:
                expected = seq_por_usuario[key] - timedelta(days=1)
                if rec.data == expected:
                    seq_por_usuario[rec.usuario_id] += 1
                    seq_por_usuario[key] = rec.data
                else:
                    continue
        else:
            continue

    alertas_ids = [uid for uid, v in seq_por_usuario.items() if isinstance(v, int) and v >= 3]
    alertas = []
    if alertas_ids:
        cols = {c.id: c for c in Colaborador.query.filter(Colaborador.id.in_(alertas_ids)).all()}
        for uid in alertas_ids:
            col = cols.get(uid)
            if not col:
                continue
            alertas.append({
                'usuario_id': uid,
                'nome': f"{col.nome} {col.sobrenome}",
                'dias': seq_por_usuario.get(uid, 0)
            })

    return render_template('admin/sentimento.html',
                           total_colabs=total_colabs,
                           participantes=participantes,
                           dist=dist,
                           reacoes_hoje=hoje,
                           alertas=alertas,
                           colaboradores=colaboradores,
                           detailed=detailed)
