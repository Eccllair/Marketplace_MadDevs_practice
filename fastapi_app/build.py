from configparser import ConfigParser
from database import SQLALCHEMY_DATABASE_URL


config = ConfigParser()
config.read('alembic.ini')
config.set('alembic', 'sqlalchemy.url', SQLALCHEMY_DATABASE_URL)

with open('alembic.ini', 'w') as configfile:
    config.write(configfile)