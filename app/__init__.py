import os
import warnings
import rollbar
from flask import Flask, got_request_exception, Request

from config import EnvironmentName


def _base_app(config_name):
    """
    initialise a barebone flask app.
    if it is needed to create multiple flask apps,
    use this function to create a base app which can be further modified later

    :arg config_name [string] - the name of the environment; must be a key in the "config" dict
    """
    from config import configs
    app = Flask(__name__)
    app.config.from_object(configs[config_name])
    configs[config_name].init_app(app)

    return app


def create_app(config_name):
    """
    creates the Flask app.
    """
    from config import EnvironmentName
    from app.db_facade import db_facade
    from app.auth.firebase import init_firebase
    print("Creating an app for environment: [%s]" % config_name)
    if config_name not in EnvironmentName.all_names():
        raise KeyError('config_name must be one of [%s]' % ", ".join(EnvironmentName.all_names()))

    app = _base_app(config_name=config_name)
    db_facade.init_app(app)
    if config_name is not EnvironmentName.testing:
        init_rollbar(app)

    if config_name is not EnvironmentName.testing:
        init_firebase(app)

    from .main import main as main_blueprint
    from .api import api as api_blueprint
    from .expenses_api import expenses_api as expenses_api_blueprint
    from .auth_api import auth_api as auth_api_blueprint

    api_version = app.config['EXPENSES_API_VERSION']
    print("Expenses API version %s " % api_version)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(auth_api_blueprint, url_prefix="/auth_api/%s" % api_version)
    app.register_blueprint(expenses_api_blueprint, url_prefix="/expenses_api/%s" % api_version)

    return app


def init_rollbar(app):
    rollbar_token_env = 'ROLLBAR_CLIENT_TOKEN'
    stage = app.config.get("APP_STAGE")

    if not app.config.get(rollbar_token_env, False):
        if stage not in [EnvironmentName.staging, EnvironmentName.production]:
            warnings.warn("ROLLBAR_CLIENT_TOKEN is not set. Rollbar will not be used")
            return
        else:
            raise Exception("ROLLBAR_CLIENT_TOKEN is required in stage %s" % stage)

    rollbar.init(
        # access token for the demo app: https://rollbar.com/demo
        app.config[rollbar_token_env],
        # environment name
        stage,
        # server root directory, makes tracebacks prettier
        root=os.path.dirname(os.path.realpath(__file__)),
        # flask already sets up logging
        allow_logging_basic_config=False,
        # play nice with aws lambda
        handler='blocking')

    # send exceptions from `app` to rollbar, using flask's signal system.
    from rollbar.contrib.flask import report_exception
    got_request_exception.connect(report_exception)

    class CustomRequest(Request):
        @property
        def rollbar_person(self):
            # 'id' is required, 'username' and 'email' are indexed but optional.
            # all values are strings.
            usr = {"id": "unknown"}
            if getattr(self, "user_uid"):
                return {"id": self.user_uid, "user_uid": self.user_uid}
            else:
                return usr

    app.request_class = CustomRequest
