# config.py
import os

local_dynamodb_url = 'http://localhost:8000'
fake_uid = 'fake firebase uid'


class BaseConfig(object):
    EXPENSES_API_VERSION = 'v1'

    APP_STAGE = os.environ['APP_STAGE']
    TESTING = False
    SECRET_KEY = os.environ['SECRET_KEY']  # this will fail if the SECRET_KEY environmental variables is not set
    CI = False  # are we in a continuous integration environment
    SITE_NAME = os.environ.get("SITE_NAME", "site_name.com")

    DB_PING_LAZY = os.environ.get("DB_PING_LAZY", False)
    CUSTOM_AUTH_HEADER_NAME = "x-firebase-auth-token"
    MAX_EXECUTION_TIME = 3  # lambda consideration

    @classmethod
    def init_app(cls, app):
        pass


class DevelopmentConfig(BaseConfig):
    LOCAL_DYNAMODB_URL = local_dynamodb_url
    TEST_FIREBASE_UID = fake_uid

    @classmethod
    def init_app(cls, app):
        super(DevelopmentConfig, cls).init_app(app)


class TestingConfig(DevelopmentConfig):
    LOCAL_DYNAMODB_URL = local_dynamodb_url
    TEST_FIREBASE_UID = fake_uid

    TESTING = True
    CI = os.environ.get("CI", False)

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
