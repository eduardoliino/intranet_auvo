from __future__ import annotations
from typing import Optional, Dict

from app import db
from datetime import datetime


class GamLog(db.Model):
    __tablename__ = 'tb_gam_log'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)
    acao = db.Column(db.String(50), nullable=False)
    ref_tipo = db.Column(db.String(20), nullable=False)
    ref_id = db.Column(db.Integer, nullable=False)
    meta_json = db.Column(db.JSON, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


def registrar_acao(usuario_id: int, acao: str, ref_tipo: str, ref_id: int, meta: Optional[Dict] = None) -> None:
    """Gancho de gamificação. Fase 1 grava apenas log de ações."""
    log = GamLog(usuario_id=usuario_id, acao=acao, ref_tipo=ref_tipo, ref_id=ref_id, meta_json=meta)
    db.session.add(log)
    db.session.commit()
    return
