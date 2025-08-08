from flask import Blueprint

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Import route modules to register them with the blueprint
from . import (
    cargos_departamentos,
    avisos,
    destaques,
    faq,
    ouvidoria,
    eventos,
    links,
)

__all__ = ['admin']
