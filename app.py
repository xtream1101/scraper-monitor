import logging
import eventlet
from flask import Flask
from flask.ext.cors import CORS
from flask.ext.restful import Api
from flask.ext.sqlalchemy import SQLAlchemy
from flask_mail import Mail
# from api import APIScraperLogging, APIScraperDataStart, APIScraperDataStop, APIScraperErrorUrl
from flask_socketio import SocketIO

async_mode = 'eventlet'

# monkey patching is necessary because this application uses a background thread
eventlet.monkey_patch()

logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ['email', 'username']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_pyfile('config.py')

api = Api(app, prefix='/api/v1')
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


socketio = SocketIO(app, async_mode=async_mode)

mail = Mail(app)
db = SQLAlchemy(app)
