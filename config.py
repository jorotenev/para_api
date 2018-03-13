# config.py
import os

local_dynamodb_url = 'http://localhost:8000'
fake_uid = 'fake firebase uid'


class BaseConfig(object):
    EXPENSES_API_VERSION = 'v1'
    APP_STAGE = os.environ['APP_STAGE']

    FIREBASE_CONFIG_JSON = os.environ['FIREBASE_CONFIG_JSON_BASE64']
    ROLLBAR_CLIENT_TOKEN = os.environ.get('ROLLBAR_CLIENT_TOKEN', '')
    # if true, the contents of `CUSTOM_AUTH_HEADER_NAME` will be treated as readily validated and extracted firebase uid
    # if false, the contents of CUSTOM_AUTH_HEADER_NAME will be validated via the firebase admin sdk and a firebase user uid
    # will be extracted from the contents of the header
    SHORT_CIRCUIT_FIREBASE = False
    TESTING = False
    SECRET_KEY = os.environ['SECRET_KEY']  # this will fail if the SECRET_KEY environmental variables is not set
    CI = False  # are we in a continuous integration environment
    SITE_NAME = os.environ.get("SITE_NAME", "site_name.com")
    DUMMY_FIREBASE_UID = os.environ.get("DUMMY_FIREBASE_UID", "")
    # makes it possible to create an app when the expenses table is empty
    DB_PING_LAZY = os.environ.get("DB_PING_LAZY", False)
    CUSTOM_AUTH_HEADER_NAME = "x-firebase-auth-token"
    MAX_EXECUTION_TIME = 3  # lambda consideration

    @classmethod
    def init_app(cls, app):
        pass


class DevelopmentConfig(BaseConfig):
    SHORT_CIRCUIT_FIREBASE = bool(int(os.environ.get("SHORT_CIRCUIT_FIREBASE", "0")))
    LOCAL_DYNAMODB_URL = os.environ.get("LOCAL_DYNAMODB_URL", local_dynamodb_url)
    DUMMY_FIREBASE_UID = fake_uid

    @classmethod
    def init_app(cls, app):
        super(DevelopmentConfig, cls).init_app(app)


class TestingConfig(DevelopmentConfig):
    CI = os.environ.get("CI", False)

    DUMMY_FIREBASE_UID = fake_uid
    SHORT_CIRCUIT_FIREBASE = bool(int(os.environ.get("SHORT_CIRCUIT_FIREBASE", "0")))

    TESTING = True
    LOCAL_DYNAMODB_URL = os.environ.get("LOCAL_DYNAMODB_URL", local_dynamodb_url)

    @classmethod
    def init_app(cls, app):
        super(TestingConfig, cls).init_app(app)


class StagingConfig(BaseConfig):

    @classmethod
    def init_app(cls, app):
        super(StagingConfig, cls).init_app(app)


class ProductionConfig(BaseConfig):

    @classmethod
    def init_app(cls, app):
        super(ProductionConfig, cls).init_app(app)


class EnvironmentName:
    """
    use this class to refer to names of environments to ensure you don't mistype a string
    """
    development = 'development'
    testing = 'testing'
    staging = 'staging'
    production = 'production'
    default = 'default'

    @classmethod
    def all_names(cls):
        return [attr for attr in dir(cls)
                if not (attr.startswith('__') or attr == 'all_names')]


configs = {
    EnvironmentName.development: DevelopmentConfig,
    EnvironmentName.testing: TestingConfig,
    EnvironmentName.staging: StagingConfig,
    EnvironmentName.production: ProductionConfig,
    EnvironmentName.default: DevelopmentConfig
}
