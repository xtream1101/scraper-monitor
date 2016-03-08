import os
import uuid
import datetime
import logging
from hashids import Hashids
from flask.ext.cors import CORS
from flask import Flask, render_template, request, flash, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from flask.ext.security import current_user, login_required, RoleMixin, Security, \
    SQLAlchemyUserDatastore, UserMixin, utils
from flask_mail import Mail
from flask.ext.admin import Admin
from flask.ext.admin.contrib import sqla

from wtforms.fields import PasswordField


try:
    # Make dir to store logs in
    os.makedirs('./logs/')
except OSError:
    pass

logging.basicConfig(level=logging.DEBUG,
                    filename='./logs/datalogging.log',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s'
                    )

logger = logging.getLogger(__name__)


# Create Flask application
app = Flask(__name__)
app.config.from_pyfile('config.py')

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
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    # __tablename__ = 'role'
    # __table_args__ = {'schema': 'scraper_monitor'}
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    # __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    apikeys = db.relationship('ApiKey', backref='user', cascade='all, delete',
                              lazy='dynamic')
    scrapers = db.relationship('Scraper', backref='user', cascade='all, delete',
                               lazy='dynamic')
    groups = db.relationship('Group', backref='user', cascade='all, delete',
                             lazy='dynamic')

    def __str__(self):
        return self.email


class ApiKey(db.Model):
    __tablename__ = 'apikey'
    # __table_args__ = {'schema': 'scraper_monitor'}
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    host = db.Column(db.String(255))
    key = db.Column(db.String(36), default=generate_uid, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, host):
        self.name = name
        self.host = host


class Group(db.Model):
    __tablename__ = 'group'
    # __table_args__ = {'schema': 'scraper_monitor'}
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scrapers = db.relationship('Scraper', backref='group', lazy='dynamic')

    def __init__(self, name):
        self.name = name


class Scraper(db.Model):
    __tablename__ = 'scraper'
    # __table_args__ = {'schema': 'scraper_monitor'}
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    owner = db.Column(db.String(64))
    key = db.Column(db.String(32), unique=True)
    date_added = db.Column(db.DateTime, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    scraper_runs = db.relationship('ScraperRun', backref='scraper',
                                   cascade='all, delete', lazy='dynamic')

    def __init__(self, name, owner):
        self.name = name
        self.owner = owner


class ScraperRun(db.Model):
    __tablename__ = 'run'
    # __table_args__ = {'schema': 'scraper_monitor'}
    id = db.Column(db.Integer(), primary_key=True)
    key = db.Column(db.String(32), default=generate_uid, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.datetime.now)
    scraper_key = db.Column(db.String(32), db.ForeignKey('scraper.key'))
    scraper_logs = db.relationship('ScraperLog', backref='scraper',
                                   cascade='all, delete', lazy='dynamic')


class ScraperLog(db.Model):
    __tablename__ = 'run_log'
    # __table_args__ = {'schema': 'scraper_monitor'}
    id = db.Column(db.Integer(), primary_key=True)
    value = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.datetime.now)
    scraper_key = db.Column(db.String(32), db.ForeignKey('scraper.key'))
    scraper_run = db.Column(db.String(32), db.ForeignKey('run.key'))

    def __init__(self, value):
        self.value = str(value)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


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
def index():
    return render_template('index.html')


###
# Api Key Routes
###
@app.route('/apikeys', methods=['GET', 'POST'])
@login_required
def apikeys():
    logger.info("Api Keys page with type {}".format(request.method))
    if request.method == 'POST':
        if not request.form['name']:
            flash("Name is required", 'error')
        else:
            apikey = ApiKey(request.form['name'], request.form['host'])
            apikey.user = current_user
            db.session.add(apikey)
            db.session.commit()
            flash("Api key was successfully created")
            return redirect(url_for('apikeys'))

    return render_template('apikeys.html',
                           apikeys=ApiKey.query.filter_by(user_id=current_user.id).all()
                           )


@app.route('/apikey/delete/<int:apikey_id>', methods=['GET'])
@login_required
def apikey_delete(apikey_id):
    api_key = ApiKey.query.filter_by(user_id=current_user.id)\
                          .filter_by(id=apikey_id).scalar()
    db.session.delete(api_key)
    db.session.commit()
    logger.info("User {} deleted API Key {}".format(current_user, api_key.name))
    flash("Deleted API key " + api_key.name)
    return redirect(url_for('apikeys'))


###
# Sensor Routes
###
@app.route('/scrapers', methods=['GET', 'POST'])
@login_required
def scrapers():
    if request.method == 'POST':
        name = request.form['name'].strip()
        owner = request.form['owner'].strip()
        group = request.form['group'].strip()
        if not name:
            flash("Name is required", 'error')
        else:
            scraper = Scraper(name, owner)
            scraper.user = current_user

            if group != "":
                scraper.group = Group.query.filter_by(id=int(group)).scalar()

            db.session.add(scraper)
            # Flush to get the id so it can be encoded
            db.session.flush()
            scraper.key = generate_key(scraper.id, 'Scraper Salt 123')

            db.session.add(scraper)
            db.session.commit()
            logger.info("User {} created scraper {} - {}"
                        .format(current_user.email, scraper.key, scraper.name))
            flash("Scraper {} was successfully created".format(scraper.name))
            return redirect(url_for('scrapers'))

    return render_template('scrapers.html',
                           scrapers=Scraper.query.filter_by(user_id=current_user.id).all(),
                           groups=Group.query.filter_by(user_id=current_user.id)
                                             .order_by(Group.name.asc()).all()
                           )


@app.route('/scraper/delete/<int:scraper_id>', methods=['GET'])
@login_required
def scraper_delete(scraper_id):
    scraper = Scraper.query.filter_by(user_id=current_user.id).filter_by(id=scraper_id).scalar()
    db.session.delete(scraper)
    db.session.commit()
    logger.info("User {} deleted scraper {} - {}"
                .format(current_user.email, scraper.key, scraper.name))
    flash("Deleted scraper " + scraper.name)
    return redirect(url_for('scrapers'))


###
# Group Routes
###
@app.route('/groups', methods=['GET', 'POST'])
@login_required
def groups():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash("Name is required", 'error')
        else:
            # Check if group name for user already exists
            is_group = Group.query.filter_by(user_id=current_user.id).filter_by(name=name).scalar()
            if is_group is not None:
                flash("Group with name {} already exists".format(name), 'error')
            else:
                group = Group(name)
                group.user = current_user

                db.session.add(group)
                db.session.commit()
                logger.info("User {} created group {}"
                            .format(current_user.email, group.name))
                flash("Group {} was successfully created".format(group.name))
                return redirect(url_for('groups'))

    return render_template('groups.html',
                           groups=Group.query.filter_by(user_id=current_user.id).all(),
                           )


@app.route('/group/delete/<int:group_id>', methods=['GET'])
@login_required
def group_delete(group_id):
    group = Group.query.filter_by(user_id=current_user.id).filter_by(id=group_id).scalar()
    db.session.delete(group)
    db.session.commit()
    logger.info("User {} deleted group {}"
                .format(current_user.email, group.name))
    flash("Deleted group {}".format(group.name))
    return redirect(url_for('groups'))


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
    encrypted_password = utils.encrypt_password('password')
    if not user_datastore.get_user('admin@example.com'):
        user_datastore.create_user(email='admin@example.com', password=encrypted_password)

    # Commit any database changes; the User and Roles must exist before we can add a Role to the User
    db.session.commit()

    # Give one User has the "end-user" role, while the other has the "admin" role. (This will have no effect if the
    # Users already have these Roles.) Again, commit any database changes.
    user_datastore.add_role_to_user('admin@example.com', 'admin')
    db.session.commit()

if __name__ == '__main__':
    # Start app
    app.run()
