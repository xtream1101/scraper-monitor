from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired
from flask_security import Security, user_registered, SQLAlchemyUserDatastore
from flask_security.forms import unique_user_email, RegisterForm

from app import app, db
from models import User, Role, Organization, Group

from pprint import pprint
user_datastore = SQLAlchemyUserDatastore(db, User, Role)

# Setup Flask-Security
# an alias to reflect a more accurate usage of the validator
unique_user_attribute = unique_user_email


class ExtendedRegisterForm(RegisterForm):
    first_name = StringField('First Name', [DataRequired()])
    last_name = StringField('Last Name', [DataRequired()])
    username = StringField('Username', [DataRequired(), unique_user_attribute])
    email = StringField('Email', [DataRequired(), unique_user_email])

    def validate(self):

        # Need this for the checks to work
        Form.validate(self)

        vaild_emails = app.config.get('SECURITY_REGISTERABLE_EMAILS')
        pprint(self.email.data)
        try:
            # This will trigger an IndexError, thats fine since an email has to have an `@`
            email_domain = self.email.data.split('@')[1].strip()
            # Dont check email domain if there is nothign to check against
            if email_domain != '' and email_domain not in vaild_emails and\
               vaild_emails is not None and len(vaild_emails) > 0:
                raise(ValueError)

        except (IndexError, ValueError):
            self.email.errors.append("Not a vaild email for this server")
            return False


security = Security(app, user_datastore, confirm_register_form=ExtendedRegisterForm)


def check_email_domain(thing):
    from pprint import pprint
    pprint(thing)


@user_registered.connect_via(app)
def user_registered_sighandler(app, user, confirm_token):
    # Get user and add organization
    user_data = User.query.get(user.id)
    # Create a private organization for user by default
    organization = Organization(name=user.username, user=user)
    user_data.organizations = [organization]
    db.session.add(organization)
    group = Group(name='Default', organization_id=organization.id)

    # If first user to register, make site admin
    if user.id == 1:
        user_datastore.add_role_to_user(user.email, 'admin')

    db.session.add(group)
    db.session.commit()
