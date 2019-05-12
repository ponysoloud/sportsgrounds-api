import os

base_dir = os.path.abspath(os.path.dirname(__file__))
postgres_local_base = 'postgresql://localhost/'
database_name = 'sg'


class Config(object):
    """
    Base application configuration
    """
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_strong_key')
    BCRYPT_HASH_PREFIX = 14
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    AUTH_TOKEN_EXPIRY_DAYS = 30
    AUTH_TOKEN_EXPIRY_SECONDS = 3000
    BUCKET_AND_ITEMS_PER_PAGE = 25
    GROUNDS_PER_PAGE = 25
    EVENTS_PER_PAGE = 25
    TEAMS_PER_PAGE = 25
    MESSAGES_PER_PAGE = 25
    USERS_PER_PAGE = 25
    UPLOAD_FOLDER = 'app/uploads/files'


class DevelopmentConfig(Config):
    """
    Development application configuration
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', postgres_local_base + database_name)
    BCRYPT_HASH_PREFIX = 4
    AUTH_TOKEN_EXPIRY_DAYS = 1
    AUTH_TOKEN_EXPIRY_SECONDS = 20
    BUCKET_AND_ITEMS_PER_PAGE = 4
    GROUNDS_PER_PAGE = 4
    EVENTS_PER_PAGE = 4
    TEAMS_PER_PAGE = 4
    USERS_PER_PAGE = 6
    MESSAGES_PER_PAGE = 10


class TestingConfig(Config):
    """
    Testing application configuration
    """
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL_TEST', postgres_local_base + database_name + "_test")
    BCRYPT_HASH_PREFIX = 4
    AUTH_TOKEN_EXPIRY_DAYS = 0
    AUTH_TOKEN_EXPIRY_SECONDS = 3
    AUTH_TOKEN_EXPIRATION_TIME_DURING_TESTS = 5
    BUCKET_AND_ITEMS_PER_PAGE = 3
    GROUNDS_PER_PAGE = 3
    EVENTS_PER_PAGE = 4
    TEAMS_PER_PAGE = 4
    USERS_PER_PAGE = 6
    MESSAGES_PER_PAGE = 10


class ProductionConfig(Config):
    """
    Production application configuration
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', postgres_local_base + database_name)
    BCRYPT_HASH_PREFIX = 13
    AUTH_TOKEN_EXPIRY_DAYS = 30
    AUTH_TOKEN_EXPIRY_SECONDS = 20
    BUCKET_AND_ITEMS_PER_PAGE = 10
    GROUNDS_PER_PAGE = 10
    EVENTS_PER_PAGE = 10
    TEAMS_PER_PAGE = 10
    USERS_PER_PAGE = 10
    MESSAGES_PER_PAGE = 25
