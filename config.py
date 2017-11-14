import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = 'easy to guess string'
    UPLOADED_PHOTOS_DEST = basedir
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    EFC_MAIL_SUBJECT_PREFIX = '[EFC]'
    EFC_MAIL_SENDER = 'EFC Admin <2654525303@qq.com>'
    EFC_ADMIN = '2654525303@qq.com'
    EFC_COMMENTS_PER_PAGE = 20
    EFC_SLOW_DB_QUERY_TIME = 0.5

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '2654525303@qq.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'bcubvkliojieeadb'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'mysql://root:123@localhost:3306/efc?charset=utf8mb4'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'mysql://root:123@localhost:3306/efc?charset=utf8mb4'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'mysql://root:123@localhost:3306/efc?charset=utf8mb4'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}