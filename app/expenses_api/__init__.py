from flask import Blueprint

expenses_api = Blueprint('expenses_api', __name__)

from . import views
