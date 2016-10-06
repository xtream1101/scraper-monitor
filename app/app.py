import logging
import eventlet
from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy, event
from flask_mail import Mail
from flask_socketio import SocketIO

async_mode = 'eventlet'

# monkey patching is necessary because this application uses a background thread
eventlet.monkey_patch()

logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ['email', 'username']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_pyfile('../config.py')

if app.config.get('SCHEMA') is None:
    app.config['SCHEMA'] = 'scraper_monitor'

api = Api(app, prefix='/api/v1')
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


socketio = SocketIO(app, async_mode=async_mode)

mail = Mail(app)
db = SQLAlchemy(app)


def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    statement = "SET search_path TO '%s'; %s" % (app.config['SCHEMA'], statement)
    return statement, parameters


event.listen(db.engine, 'before_cursor_execute', before_cursor_execute, retval=True)
