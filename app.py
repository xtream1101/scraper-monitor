import os
import uuid
import logging
import datetime
import eventlet
from functools import wraps
from hashids import Hashids

from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

from flask_mail import Mail
from flask.ext.cors import CORS
from flask.ext.admin import Admin
from flask.ext.admin.contrib import sqla
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Resource, Api, abort
from flask.ext.security import user_registered
from flask.ext.security.forms import ConfirmRegisterForm, LoginForm, StringField, Required, unique_user_email
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask.ext.security import current_user, login_required, RoleMixin, Security, \
    SQLAlchemyUserDatastore, UserMixin, utils

from wtforms.fields import PasswordField

from pprint import pprint

async_mode = 'eventlet'
# monkey patching is necessary because this application uses a background thread
eventlet.monkey_patch()

os.environ['TZ'] = 'UTC'

try:
    # Make dir to store logs in
    os.makedirs('./logs/')
except OSError:
    pass

logging.basicConfig(level=logging.WARNING,
                    # filename='./logs/scraper_monitor.log',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s'
                    )

logger = logging.getLogger(__name__)


# Create Flask application
app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ['email', 'username']

api = Api(app, prefix='/api/v1')
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

socketio = SocketIO(app, async_mode=async_mode)
mail = Mail(app)
db = SQLAlchemy(app)


#######################
# Key generators
#######################
def generate_uid():
    return uuid.uuid4().hex


def generate_key(id, salt, size=8):
    hashids = Hashids(salt=salt, min_length=size)
    return hashids.encode(id)

# Define models
# TODO: make a config value
SCHEMA = 'scraper_monitor'

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey(SCHEMA + '.user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey(SCHEMA + '.role.id')),
    schema=SCHEMA,
)

organizations_users = db.Table(
    'organizations_users',
    db.Column('user_id', db.Integer, db.ForeignKey(SCHEMA + '.user.id')),
    db.Column('organization_id', db.Integer, db.ForeignKey(SCHEMA + '.organization.id')),
    schema=SCHEMA,
)


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='subquery'))
    organizations_owner = db.relationship('Organization', backref='user',
                                          lazy='subquery')
    organizations = db.relationship('Organization', secondary=organizations_users,
                                    backref=db.backref('users', lazy='subquery'))

    def __str__(self):
        return self.username


class Organization(db.Model):
    __tablename__ = 'organization'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.user.id'))
    groups = db.relationship('Group', backref='organization', cascade='all, delete',
                             lazy='subquery')
    apikeys = db.relationship('ApiKey', backref='organization', cascade='all, delete',
                              lazy='subquery')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.id,
                'name': self.name,
                }


class ApiKey(db.Model):
    __tablename__ = 'apikey'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    host = db.Column(db.String(255))
    key = db.Column(db.String(36), default=generate_uid, unique=True)
    time_added = db.Column(db.DateTime, default=datetime.datetime.now)
    organization_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.organization.id'))

    def __init__(self, name, host):
        self.name = name
        self.host = host

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.id,
                'organization': self.organization.name,
                'name': self.name,
                'host': self.host,
                'key': self.key,
                'timeAdded': datetime_to_str(self.time_added),
                }


class Group(db.Model):
    __tablename__ = 'group'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    organization_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.organization.id'))
    scrapers = db.relationship('Scraper', backref='group', lazy='subquery')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.id,
                'organization': self.organization.name,
                'name': self.name,
                }


class Scraper(db.Model):
    __tablename__ = 'scraper'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    owner = db.Column(db.String(64))
    key = db.Column(db.String(32), unique=True)
    time_added = db.Column(db.DateTime, default=datetime.datetime.now)
    group_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.group.id'))
    scraper_runs = db.relationship('ScraperRun', backref='scraper',
                                   cascade='all, delete-orphan', lazy='subquery')

    def __init__(self, name, owner):
        self.name = name
        self.owner = owner

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.id,
                'name': self.name,
                'owner': self.owner,
                'key': self.key,
                'group': self.group.name,
                'timeAdded': datetime_to_str(self.time_added),
                }


class ScraperRun(db.Model):
    __tablename__ = 'run'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(32), unique=True)
    start_time = db.Column(db.DateTime)
    stop_time = db.Column(db.DateTime)
    runtime = db.Column(db.Float)
    critical_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    warning_count = db.Column(db.Integer, default=0)
    scraper_key = db.Column(db.String(32), db.ForeignKey(SCHEMA + '.scraper.key'))
    scraper_logs = db.relationship('ScraperLog', backref='scraper_run',
                                   cascade='all, delete', lazy='subquery')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.uuid,
                'uuid': self.uuid,
                'name': self.scraper.name,
                'scraperKey': self.scraper_key,
                'startTime': datetime_to_str(self.start_time),
                'stopTime': datetime_to_str(self.stop_time),
                'runtime': self.runtime,
                'criticalCount': self.critical_count,
                'errorCount': self.error_count,
                'warningCount': self.warning_count,
                }


class ScraperLog(db.Model):
    __tablename__ = 'run_log'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer(), primary_key=True)
    exc_info = db.Column(db.Text)
    exc_text = db.Column(db.Text)
    filename = db.Column(db.String(256))
    func_name = db.Column(db.String(256))
    level_name = db.Column(db.String(256))
    level_no = db.Column(db.Integer)
    line_no = db.Column(db.Integer)
    message = db.Column(db.String(512))
    module = db.Column(db.String(256))
    name = db.Column(db.String(256))
    pathname = db.Column(db.String(256))
    process = db.Column(db.Integer)
    process_name = db.Column(db.String(256))
    relative_created = db.Column(db.Float)
    stack_info = db.Column(db.String(256))
    thread = db.Column(db.Integer)
    thread_name = db.Column(db.String(256))
    time_collected = db.Column(db.DateTime, default=datetime.datetime.now)
    run_uuid = db.Column(db.String(32), db.ForeignKey(SCHEMA + '.run.uuid'))

# Setup Flask-Security
# an alias to reflect a more accurate usage of the validator
unique_user_attribute = unique_user_email


class ExtendedRegisterForm(ConfirmRegisterForm):
    first_name = StringField('First Name', [Required()])
    last_name = StringField('Last Name', [Required()])
    username = StringField('Username', [Required(), unique_user_attribute])

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, confirm_register_form=ExtendedRegisterForm)


# Customized User model for SQL-Admin
class UserAdmin(sqla.ModelView):
    # Don't display the password on the list of Users
    column_exclude_list = ('password',)
    # Don't include the standard password field when creating or editing a User (but see below)
    form_excluded_columns = ('password',)
    # Automatically display human-readable names for the current and available Roles when creating or editing a User
    column_auto_select_related = True

    # Prevent administration of Users unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a regular text field.
    def scaffold_form(self):
        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(UserAdmin, self).scaffold_form()
        # Add a password field, naming it "password2" and labeling it "New Password".
        form_class.password2 = PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):
        # If the password field isn't blank...
        if len(model.password2):
            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = utils.encrypt_password(model.password2)


# Customized Role model for SQL-Admin
class RoleAdmin(sqla.ModelView):

    # Prevent administration of Roles unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

# Initialize Flask-Admin
admin = Admin(app)

# Add Flask-Admin views for Users and Roles
admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))


# Flask views
@app.route('/register')
def register():
    return render_template('security/register_user.html')


@app.route('/')
@login_required
def index():
    return render_template('index.html')
    # return render_template('scrapers.html')

###############################################################################
###############################################################################
##
##                Manage Scrapers
##
###############################################################################
###############################################################################
###
# Api Key Routes
###
@socketio.on('connect', namespace='/manage/apikeys')
def connect_manage_apikeys():
    if not current_user.is_authenticated:
        # If user is not logged in, deny them access
        return False

    apikey_list = []
    for organization in current_user.organizations:
        apikeys = ApiKey.query.filter_by(organization=organization).all()
        apikeys = [i.serialize for i in apikeys]
        apikey_list.extend(apikeys)

    emit('manage-apikeys', {'data': apikey_list, 'action': 'add'})


@app.route('/manage/apikeys', methods=['GET', 'POST'])
@login_required
def manage_apikeys():
    if request.method == 'POST':
        rdata = {'success': False,
                 'message': '',
                 }
        name = request.form['name'].strip()
        host = request.form['host'].strip()
        organization_id = request.form['organization'].strip()
        if not name:
            rdata['message'] = "Name is required"
            rdata['success'] = False
        else:
            apikey = ApiKey(name, host)
            apikey.organization = Organization.query.get(organization_id)

            db.session.add(apikey)
            db.session.commit()
            data = [apikey.serialize]
            socketio.emit('manage-apikeys',
                          {'data': data, 'action': 'add'},
                          namespace='/manage/apikeys'
                          )
            rdata['message'] = "Api key {} was successfully created in {}".format(apikey.name, apikey.organization.name)
            rdata['success'] = True
        return jsonify(rdata)

    return render_template('manage/apikeys.html')


@app.route('/manage/apikeys/delete/<int:apikey_id>', methods=['GET'])
@login_required
def manage_apikey_delete(apikey_id):
    apikey = ApiKey.query.get(apikey_id)
    # Check if user can delete apikey
    if current_user not in apikey.organization.users:
        abort(403)

    db.session.delete(apikey)
    db.session.commit()
    logger.info("User {} deleted API Key {} from {}".format(current_user, apikey.name, apikey.organization.name))
    data = [apikey.serialize]
    socketio.emit('manage-apikeys',
                  {'data': data, 'action': 'delete'},
                  namespace='/manage/apikeys'
                  )
    return jsonify({'message': "Deleted API key {} from {}".format(apikey.name,
                                                                   apikey.organization.name)
                    })


###
# Sensor Routes
###
@socketio.on('connect', namespace='/manage/scrapers')
def connect_manage_scrapers():
    if not current_user.is_authenticated:
        # If user is not logged in, deny them access
        return False

    scraper_list = []
    for organization in current_user.organizations:
        for group in organization.groups:
            scrapers = Scraper.query.filter_by(group=group).all()
            scrapers = [i.serialize for i in scrapers]
            scraper_list.extend(scrapers)

    emit('manage-scrapers', {'data': scraper_list, 'action': 'add'})


@app.route('/manage/scrapers', methods=['GET', 'POST'])
@login_required
def manage_scrapers():
    if request.method == 'POST':
        rdata = {'success': False,
                 'message': '',
                 }
        name = request.form['name'].strip()
        group_id = request.form['group'].strip()
        owner = request.form['owner'].strip()
        if not name:
            rdata['message'] = "Name is required"
            rdata['success'] = False
        else:
            scraper = Scraper(name, owner)
            scraper.user = current_user

            if group_id != "":
                scraper.group = Group.query.get(group_id)

            db.session.add(scraper)
            # Flush to get the id so it can be encoded
            db.session.flush()
            scraper.key = generate_key(scraper.id, 'Scraper Salt 123')

            db.session.add(scraper)
            db.session.commit()
            logger.info("User {} created scraper {} - {}"
                        .format(current_user.email, scraper.key, scraper.name))
            data = [scraper.serialize]
            socketio.emit('manage-scrapers',
                          {'data': data, 'action': 'add'},
                          namespace='/manage/scrapers'
                          )
            rdata['message'] = "Scraper {} was successfully created in group {}"\
                               .format(scraper.name, scraper.group.name)
            rdata['success'] = True
        return jsonify(rdata)

    group_list = []
    for organization in current_user.organizations:
        groups = Group.query.filter_by(organization=organization).all()
        groups = [i.serialize for i in groups]
        group_list.extend(groups)
    return render_template('manage/scrapers.html',
                           groups=group_list
                           )


@app.route('/manage/scrapers/delete/<int:scraper_id>', methods=['GET'])
@login_required
def manage_scraper_delete(scraper_id):
    scraper = Scraper.query.get(scraper_id)
    # Check if user can delete group
    if current_user not in scraper.group.organization.users:
        abort(403)

    db.session.delete(scraper)
    db.session.commit()
    logger.info("User {} deleted scraper {} - {}"
                .format(current_user.email, scraper.key, scraper.name))
    data = [scraper.serialize]
    socketio.emit('manage-scrapers',
                  {'data': data, 'action': 'delete'},
                  namespace='/manage/scrapers'
                  )
    return jsonify({'message': "Deleted Scraper " + scraper.name})


###
# Group Routes
###
@socketio.on('connect', namespace='/manage/groups')
def connect_manage_groups():
    if not current_user.is_authenticated:
        # If user is not logged in, deny them access
        return False

    group = []
    for organization in current_user.organizations:
        groups = Group.query.filter_by(organization=organization).all()
        groups = [i.serialize for i in groups]
        group.extend(groups)

    emit('manage-groups', {'data': group, 'action': 'add'})


@app.route('/manage/groups', methods=['GET', 'POST'])
@login_required
def manage_groups():
    if request.method == 'POST':
        rdata = {'success': False,
                 'message': '',
                 }
        name = request.form['name'].strip()
        organization_id = request.form['organization'].strip()
        if not name:
            rdata['message'] = "Name is required"
            rdata['success'] = False
        else:
            # Check if group name for organization already exists
            is_group = Group.query.filter_by(organization_id=organization_id).filter_by(name=name).scalar()
            if is_group is not None:
                rdata['message'] = "Group with name {} already exists".format(name)
                rdata['success'] = False
            else:
                group = Group(name=name, organization_id=organization_id)
                group.organization = Organization.query.get(organization_id)

                db.session.add(group)
                db.session.commit()
                logger.info("User {} created group {} in {}"
                            .format(current_user.email, group.name, group.organization.name))
                data = [group.serialize]
                socketio.emit('manage-groups',
                              {'data': data, 'action': 'add'},
                              namespace='/manage/groups'
                              )
                rdata['message'] = "Group {} was successfully created in {}".format(group.name, group.organization.name)
                rdata['success'] = True
        return jsonify(rdata)

    return render_template('manage/groups.html')


@app.route('/manage/groups/delete/<int:group_id>', methods=['GET'])
@login_required
def manage_group_delete(group_id):
    rdata = {'success': False,
             'message': '',
             }
    group = Group.query.get(group_id)
    # Check if user can delete group
    if current_user not in group.organization.users:
        abort(403)

    if group.name == 'default':
        rdata['message'] = "Cannot delete default group"
    else:
        db.session.delete(group)
        db.session.commit()
        logger.info("User {} deleted group {} from {}"
                    .format(current_user.email, group.name, group.organization.name))
        data = [group.serialize]
        socketio.emit('manage-groups',
                      {'data': data, 'action': 'delete'},
                      namespace='/manage/groups'
                      )

        rdata['message'] = "Deleted Group {} from {}".format(group.name, group.organization.name)
        rdata['success'] = True

    return jsonify(rdata)


###############################################################################
###############################################################################
##
##                Scraper Run Data
##
###############################################################################
###############################################################################

@socketio.on('connect', namespace='/data/scrapers')
def connect_data_scrapers():
    if not current_user.is_authenticated:
        # If user is not logged in, deny them access
        return False

    # scrapers = Scraper.query.filter_by(user_id=current_user.id).all()
    scrapers = ScraperRun.query.filter_by(stop_time=None).all()
    scrapers = [i.serialize for i in scrapers]
    emit('data-scrapers', {'data': scrapers, 'action': 'add'})


@app.route('/data/scrapers', methods=['GET'])
@login_required
def data_scrapers():
    return render_template('data/scrapers.html')

###############################################################################
###############################################################################
##
##                Scraper API
##
###############################################################################
###############################################################################
#######################
# API Decorators
#######################
def authenticate_api(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Get apikey and check it against the database
            apikey = request.args['apikey']
            found_key = ApiKey.query.filter_by(key=apikey).scalar()
            if found_key is not None:
                # If valid, return
                return func(*args, **kwargs)
            # If invalid, abort
            logger.warning("authenticate_api: abort 401")
            abort(401)
        except KeyError:
            # If apikey is not even passed
            logger.warning("authenticate_api KeyError: abort 401", exc_info=True)
            abort(401)
    return wrapper


def validate_api_scraper_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rdata = {'success': False,
                 'message': ""
                 }
        try:
            user_id = None
            api_key = request.args['apikey']
            if 'scraperKey' in request.args:
                scraper_key = request.args['scraperKey']
                # Check that the apikey has acccess to the sensor
                user_id = Scraper.query.filter_by(key=scraper_key).scalar().user_id
            else:
                rdata['message'] = "Missing scraper key"
                return rdata

            key_user_id = ApiKey.query.filter_by(key=api_key).scalar().user_id
            if key_user_id == user_id:
                # The api key and sensor/group both belong to the same user
                return func(*args, **kwargs)
            else:
                logger.warning("Invalid scraper key")
                rdata['message'] = "Invalid scraper key"
        except AttributeError:
            logger.warning("Invalid scraper key", exc_info=True)
            rdata['message'] = "Invalid scraper key"
        except Exception:
            logger.exception("Oops, somthing went wrong when validating your scraper")
            rdata['message'] = "Oops, somthing went wrong when validating your scraper"

        return rdata
    return wrapper


#######################
# API Endpoints
#######################
class APIScraperLogging(Resource):
    method_decorators = [validate_api_scraper_key, authenticate_api]

    def post(self):
        rdata = {'success': False,
                 'message': ""
                 }
        # pprint(request.args)
        # pprint(request.form)
        client_data = request.args
        log_data = request.form

        log = ScraperLog()
        log.run_uuid = client_data['scraperRun']
        log.exc_info = log_data['exc_info']
        log.exc_text = log_data['exc_text']
        log.filename = log_data['filename']
        log.func_name = log_data['funcName']
        log.level_name = log_data['levelname']
        log.level_no = log_data['levelno']
        log.line_no = log_data['lineno']
        log.message = log_data['message']
        log.module = log_data['module']

        db.session.add(log)
        db.session.commit()

        data = [{'rowId': client_data['scraperRun']}]
        if log.level_name == 'CRITICAL':
            data[0]['criticalCount'] = 1
        if log.level_name == 'ERROR':
            data[0]['errorCount'] = 1
        if log.level_name == 'WARNING':
            data[0]['warningCount'] = 1

        socketio.emit('data-scrapers',
                      {'data': data, 'action': 'increment'},
                      namespace='/data/scrapers'
                      )

        rdata['success'] = True
        rdata['message'] = ""

        return rdata


class APIScraperDataStart(Resource):
    method_decorators = [validate_api_scraper_key, authenticate_api]

    def post(self):
        rdata = {'success': False,
                 'message': ""
                 }

        client_data = request.args
        data = request.json

        run = ScraperRun()
        run.scraper_key = client_data['scraperKey']
        run.uuid = client_data['scraperRun']
        run.start_time = data['startTime']

        db.session.add(run)
        db.session.commit()

        data = [run.serialize]
        socketio.emit('data-scrapers',
                      {'data': data, 'action': 'add'},
                      namespace='/data/scrapers'
                      )

        rdata['success'] = True
        rdata['message'] = ""

        return rdata


class APIScraperDataStop(Resource):
    method_decorators = [validate_api_scraper_key, authenticate_api]

    def post(self):
        rdata = {'success': False,
                 'message': ""
                 }

        client_data = request.args
        data = request.json

        run = ScraperRun.query.filter_by(uuid=client_data['scraperRun']).scalar()
        run.stop_time = datetime.datetime.strptime(data['stopTime'], "%Y-%m-%d %H:%M:%S.%f")
        # Calc runtime and get counts
        runtime = run.stop_time - run.start_time
        run.runtime = runtime.total_seconds()

        counts = ScraperLog.query.filter_by(run_uuid=client_data['scraperRun'])
        run.critical_count = counts.filter_by(level_name='CRITICAL').count()
        run.error_count = counts.filter_by(level_name='ERROR').count()
        run.warning_count = counts.filter_by(level_name='WARNING').count()

        db.session.commit()

        data = [run.serialize]
        socketio.emit('data-scrapers',
                      {'data': data, 'action': 'update'},
                      namespace='/data/scrapers'
                      )

        rdata['success'] = True
        rdata['message'] = ""

        return rdata

api.add_resource(APIScraperLogging, '/logs')
api.add_resource(APIScraperDataStart, '/data/start')
api.add_resource(APIScraperDataStop, '/data/stop')


#######################
# App Utils
#######################
def datetime_to_str(timestamp):
    if timestamp is None:
        return None
    # The script is set to use UTC, so all times are in UTC
    return timestamp.isoformat() + "+0000"


@user_registered.connect_via(app)
def user_registered_sighandler(app, user, confirm_token):
    # Get user and add organization
    user_data = User.query.get(user.id)
    # Create an organization of username for user by default
    organization = Organization(name=user.username, user=user)
    user_data.organizations = [organization]
    db.session.add(organization)
    group = Group(name='default', organization_id=organization.id)
    db.session.add(group)
    db.session.commit()


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
    db.session.commit()

if __name__ == '__main__':
    socketio.run(app, debug=True)
