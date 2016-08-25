import os
import logging
from app.app import app, db
from app.api import *
from app.admin import *
from app.auth import *
from app.models import *
from app.views import *

os.environ['TZ'] = 'UTC'

try:
    # Make dir to store logs in
    os.makedirs('./logs/')
except OSError:
    pass

logging.basicConfig(level=logging.INFO,
                    filename='./logs/scraper_monitor.log',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s'
                    )

logger = logging.getLogger(__name__)


# Executes before the first request is processed.
@app.before_first_request
def before_first_request():

    # Create any database tables that don't exist yet.
    db.create_all()

    # Create the Roles "admin" and "end-user" -- unless they already exist
    user_datastore.find_or_create_role(name='admin', description='Administrator')
    user_datastore.find_or_create_role(name='end-user', description='End user')

    # Create two Users for testing purposes -- unless they already exists.
    # In each case, use Flask-Security utility function to encrypt the password.
    # encrypted_password = utils.encrypt_password('password')
    # if not user_datastore.get_user('admin@example.com'):
    #     user_datastore.create_user(email='admin@example.com', password=encrypted_password, username='AdminNick')

    # Commit any database changes; the User and Roles must exist before we can add a Role to the User
    db.session.commit()

    # Give one User has the "end-user" role, while the other has the "admin" role. (This will have no effect if the
    # Users already have these Roles.) Again, commit any database changes.
    # user_datastore.add_role_to_user('admin@example.com', 'admin')
    # db.session.commit()

if __name__ == '__main__':
    socketio.run(app, host=app.config.get('HOST'), port=app.config.get('PORT'), debug=app.config.get('DEBUG'))
