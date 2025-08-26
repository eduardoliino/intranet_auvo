from flask import Blueprint

newsletter_bp = Blueprint('newsletter', __name__, template_folder='../templates', static_folder='../static')

from . import routes  # noqa: E402
