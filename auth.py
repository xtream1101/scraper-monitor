from flask.ext.security import Security, user_registered, SQLAlchemyUserDatastore
from flask.ext.security.forms import ConfirmRegisterForm, StringField, Required, unique_user_email

from app import app, db
from models import User, Role, Organization, Group

user_datastore = SQLAlchemyUserDatastore(db, User, Role)

# Setup Flask-Security
# an alias to reflect a more accurate usage of the validator
unique_user_attribute = unique_user_email


class ExtendedRegisterForm(ConfirmRegisterForm):
    first_name = StringField('First Name', [Required()])
    last_name = StringField('Last Name', [Required()])
    username = StringField('Username', [Required(), unique_user_attribute])

security = Security(app, user_datastore, confirm_register_form=ExtendedRegisterForm)


@user_registered.connect_via(app)
def user_registered_sighandler(app, user, confirm_token):
    # Get user and add organization
    user_data = User.query.get(user.id)
    # Create a private organization for user by default
    organization = Organization(name=user.username, user=user)
    user_data.organizations = [organization]
    db.session.add(organization)
    group = Group(name='Default', organization_id=organization.id)
    db.session.add(group)
    db.session.commit()
