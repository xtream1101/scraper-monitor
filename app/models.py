import uuid
import datetime
from hashids import Hashids
from flask_security import current_user, RoleMixin, UserMixin
from app.app import app, db


def generate_uid():
    return uuid.uuid4().hex


def generate_key(id, salt, size=8):
    hashids = Hashids(salt=salt, min_length=size)
    return hashids.encode(id)


def datetime_to_str(timestamp):
    if timestamp is None:
        return None
    # The script is set to use UTC, so all times are in UTC
    return timestamp.isoformat() + "+0000"


SCHEMA = app.config.get('SCHEMA')

# This table is here so when migrate is run it does not try and delete it
class AlembicVersion(db.Model):
    __tablename__ = 'alembic_version'
    __table_args__ = {'schema': SCHEMA}
    version_num = db.Column(db.String(32), primary_key=True)


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
                            backref=db.backref('users', lazy='dynamic'))
    organizations_owner = db.relationship('Organization', backref='user', lazy='dynamic')
    organizations = db.relationship('Organization', secondary=organizations_users,
                                    backref='users', lazy='dynamic')
    scrapers = db.relationship('Scraper', backref='owner', lazy='dynamic')

    def __str__(self):
        return self.username


class Organization(db.Model):
    __tablename__ = 'organization'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.user.id'))
    groups = db.relationship('Group', backref='organization', cascade='all, delete',
                             lazy='dynamic')
    apikeys = db.relationship('ApiKey', backref='organization', cascade='all, delete',
                              lazy='dynamic')

    def __str__(self):
        return self.name

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.id,
                'name': self.name,
                'owner': self.user.username,
                'isOwner': current_user.id == self.owner_id,
                }


class ApiKey(db.Model):
    __tablename__ = 'apikey'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    key = db.Column(db.String(36), default=generate_uid, unique=True)
    time_added = db.Column(db.DateTime, default=datetime.datetime.now)
    organization_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.organization.id'))

    def __init__(self, name):
        self.name = name

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.id,
                'organization': self.organization.name,
                'name': self.name,
                'key': self.key,
                'timeAdded': datetime_to_str(self.time_added),
                }


class Group(db.Model):
    __tablename__ = 'group'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    organization_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.organization.id'))
    scrapers = db.relationship('Scraper', backref='group', lazy='dynamic')
    scraper_runs = db.relationship('ScraperRun', backref='group', lazy='dynamic')

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
    key = db.Column(db.String(32), unique=True)
    time_added = db.Column(db.DateTime, default=datetime.datetime.now)
    owner_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.group.id'))
    scraper_runs = db.relationship('ScraperRun', backref='scraper',
                                   cascade='all, delete-orphan', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '{}.{} - {}'.format(self.group.organization.name, self.group.name, self.name)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""

        try:
            owner = User.query.get(self.owner_id).username
        except Exception:
            owner = None

        return {'id': self.id,
                'rowId': self.id,
                'name': self.name,
                'owner': owner,
                'key': self.key,
                'group': self.group.name,
                'organization': self.group.organization.name,
                'timeAdded': datetime_to_str(self.time_added),
                }


class ScraperRun(db.Model):
    __tablename__ = 'run'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(32), unique=True)
    environment = db.Column(db.String(4), default='DEV')
    start_time = db.Column(db.DateTime)
    stop_time = db.Column(db.DateTime)
    runtime = db.Column(db.Float)
    annotation = db.Column(db.Text)
    total_urls_hit = db.Column(db.Integer)
    num_rows_added_to_db = db.Column(db.Integer)
    ref_data_count = db.Column(db.Integer)
    ref_data_success_count = db.Column(db.Integer)
    url_error_count = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    warning_count = db.Column(db.Integer, default=0)
    scraper_key = db.Column(db.String(32), db.ForeignKey(SCHEMA + '.scraper.key'))
    group_id = db.Column(db.Integer, db.ForeignKey(SCHEMA + '.group.id'))
    scraper_logs = db.relationship('ScraperLog', backref='scraper_run',
                                   cascade='all, delete', lazy='dynamic')
    scraper_url_errors = db.relationship('ScraperUrlError', backref='scraper_run',
                                         cascade='all, delete', lazy='dynamic')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.uuid,
                'uuid': self.uuid,
                'organization': self.scraper.group.organization.name,
                'name': self.scraper.name,
                'scraperKey': self.scraper_key,
                'group_id': self.group_id,
                'group': self.scraper.group.name,
                'startTime': datetime_to_str(self.start_time),
                'stopTime': datetime_to_str(self.stop_time),
                'runtime': self.runtime,
                'totalUrlsHit': self.total_urls_hit,
                'numRowsAddedToDb': self.num_rows_added_to_db,
                'refDataCount': self.ref_data_count,
                'refDataSuccessCount': self.ref_data_success_count,
                'criticalCount': self.critical_count,
                'errorCount': self.error_count,
                'warningCount': self.warning_count,
                'urlErrorCount': self.url_error_count,
                'annotation': self.annotation,
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
    thread = db.Column(db.String(256))
    thread_name = db.Column(db.String(256))
    time_collected = db.Column(db.DateTime, default=datetime.datetime.now)
    run_uuid = db.Column(db.String(32), db.ForeignKey(SCHEMA + '.run.uuid'))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'rowId': self.id,
                'run_uuid': self.run_uuid,
                'exc_info': self.exc_info,
                'exc_text': self.exc_text,
                'filename': self.filename,
                'func_name': self.func_name,
                'level_name': self.level_name,
                'level_no': self.level_no,
                'line_no': self.line_no,
                'message': self.message,
                'module': self.module,
                'name': self.name,
                'pathname': self.pathname,
                'process': self.process,
                'process_name': self.process_name,
                'relative_created': self.relative_created,
                'stack_info': self.stack_info,
                'thread': self.thread,
                'thread_name': self.thread_name,
                'time_collected': datetime_to_str(self.time_collected),
                }


class ScraperUrlError(db.Model):
    __tablename__ = 'run_url_error'
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer(), primary_key=True)
    url = db.Column(db.String(1024))
    reason = db.Column(db.String(256))
    ref_id = db.Column(db.String(256))
    ref_table = db.Column(db.String(256))
    status_code = db.Column(db.Integer())
    thread_name = db.Column(db.String(256))
    num_tries = db.Column(db.Integer())
    time_collected = db.Column(db.DateTime, default=datetime.datetime.now)
    run_uuid = db.Column(db.String(32), db.ForeignKey(SCHEMA + '.run.uuid'))
