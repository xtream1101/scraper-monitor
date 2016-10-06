import os
from app.app import app, db
from app.models import *
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

os.environ['TZ'] = 'UTC'


# Create tables if they do not already exist
db.create_all()  # Used on fresh installs

migrate = Migrate(app, db)

@migrate.configure
def configure_alembic(config):
    # modify config object
    print(config)
    return config


manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
