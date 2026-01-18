from flask import Blueprint
bp = Blueprint("accounts", __name__, template_folder="templates", static_folder=None)
from . import routes  # noqa