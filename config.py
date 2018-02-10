# config.py
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env_dev')  # will fail silently if file is missing
load_dotenv(dotenv_path)


class BaseConfig(object):
    TESTING = False
    SECRET_KEY = os.environ['SECRET_KEY']  # this will fail if the SECRET_KEY environmental variables is not set
    CI = False  # are we in a continuous integration environment
    SITE_NAME = os.environ.get("SITE_NAME", "site_name.com")

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(BaseConfig):

    @staticmethod
    def init_app(app):
        pass


class TestingConfig(DevelopmentConfig):
    TESTING = True

    @staticmethod
    def init_app(app):
        pass


class StagingConfig(BaseConfig):
    CI = True

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(BaseConfig):

    @staticmethod
    def init_app(app):
        pass


class EnvironmentName:
    """
    use this class to refer to names of environments to ensure you don't mistype a string
    """
    development = 'development'
    testing = 'testing'
    staging = 'staging'
    production = 'production'
    default = 'default'


config = {
    EnvironmentName.development: DevelopmentConfig,
    EnvironmentName.testing: TestingConfig,
    EnvironmentName.staging: StagingConfig,
    EnvironmentName.production: ProductionConfig,
    EnvironmentName.default: DevelopmentConfig
}
