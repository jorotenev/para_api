from flask import Flask
from config import config
from app.db_facade import db_facade


def _base_app(config_name):
    """
    initialise a barebone flask app.
    if it is needed to create multiple flask apps,
    use this function to create a base app which can be further modified later

    :arg config_name [string] - the name of the environment; must be a key in the "config" dict
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    return app


def create_app(config_name):
    """
    creates the Flask app.
    """
    app = _base_app(config_name=config_name)
    db_facade.init_app(app)
    from .main import main as main_blueprint
    from .api import api as api_blueprint
    from .expenses_api import expenses_api as expenses_api_blueprint
    from .auth_api import auth_api as auth_api_blueprint

    api_version = 'v1'
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(auth_api_blueprint, url_prefix="/auth_api/%s" % api_version)
    app.register_blueprint(expenses_api_blueprint, url_prefix="/expenses_api/%s" % api_version)

    return app
