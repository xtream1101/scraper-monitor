import os
import shutil
from app.app import app, db
from app.models import *
from flask_script import Command, Manager
from flask_migrate import Migrate, MigrateCommand

os.environ['TZ'] = 'UTC'


class CustomEnv(Command):
    """
    Copy over custom env.py to use for migrations
    """

    def run(self):
        print("copy file")
        shutil.copyfile('migrations_custom_env.py', 'migrations/env.py')


# Create tables if they do not already exist
db.create_all()  # Used on fresh installs

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('copy_env', CustomEnv())

if __name__ == '__main__':
    manager.run()
