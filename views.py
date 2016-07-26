import logging
from flask import render_template, request, jsonify, abort, redirect, url_for
from flask.ext.security import current_user, login_required
from flask_socketio import emit, join_room
from app import app, socketio
from models import *
from pprint import pprint

logger = logging.getLogger(__name__)


# Flask views
@app.route('/register')
def register():
    return render_template('security/register_user.html')


@app.route('/')
@login_required
def index():
    return render_template('index.html')


###############################################################################
###############################################################################
##
##                Manage Scrapers
##
###############################################################################
###############################################################################
@app.route('/manage/api/userlist/<int:organization_group_id>', methods=['GET'])
@login_required
def manage_user_list(organization_group_id):
    user_list = []
    users = Group.query.get(organization_group_id).organization.users

    if current_user not in users:
        abort(403)

    for user in users:
        user_list.append({'id': user.id,
                          'username': user.username,
                          'selected': current_user == user
                          })

    rdata = {'userList': user_list}
    return jsonify(rdata)


@app.route('/manage/api/edit_field/grouplist/', methods=['GET'])
@login_required
def manage_edit_field_group_list():
    rdata = {'currentGroupId': None,
             'groupList': [],
             }

    scraper_id = request.args.get('scraper_id')
    if scraper_id is not None:
        scraper = Scraper.query.get(scraper_id)
        if current_user in scraper.group.organization.users:
            # Make sure the user has access to this scraper
            rdata['currentGroupId'] = scraper.group_id

    group_list = []
    organizations = User.query.get(current_user.id).organizations

    for organization in organizations:
        for group in organization.groups:
            group_list.append({'id': group.id,
                               'name': '{}.{}'.format(organization.name, group.name),
                               })

    rdata['groupList'] = group_list

    return jsonify(rdata)


@app.route('/manage/api/edit_field/userlist/', methods=['GET'])
@login_required
def manage_edit_field_user_list():
    rdata = {'currentUserId': None,
             'userList': [],
             }

    scraper_id = request.args.get('scraper_id')
    if scraper_id is not None:
        scraper = Scraper.query.get(scraper_id)
        if current_user in scraper.group.organization.users:
            # Make sure the user has access to this scraper
            rdata['currentUserId'] = scraper.owner_id

    user_list = []
    for user in scraper.group.organization.users:
        user_list.append({'id': user.id,
                          'name': '{}'.format(user.username),
                          })

    rdata['userList'] = user_list

    return jsonify(rdata)


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
        join_room('organization-' + str(organization.id))
        apikeys = ApiKey.query.filter_by(organization=organization).all()
        apikeys = [i.serialize for i in apikeys]
        apikey_list.extend(apikeys)

    emit('manage-apikeys', {'data': apikey_list, 'action': 'add'})


@app.route('/manage/apikeys', methods=['GET', 'POST'])
@login_required
def manage_apikeys():
    if request.method == 'POST':
        rdata = {'status': 'success',
                 'message': '',
                 }
        name = request.form['name'].strip()
        organization_id = request.form['organization'].strip()
        if not name:
            rdata['message'] = "Name is required"
            rdata['status'] = 'error'
        else:
            apikey = ApiKey(name)
            apikey.organization = Organization.query.get(organization_id)

            db.session.add(apikey)
            db.session.commit()
            data = [apikey.serialize]
            socketio.emit('manage-apikeys',
                          {'data': data, 'action': 'add'},
                          namespace='/manage/apikeys',
                          room='organization-' + str(apikey.organization_id)
                          )
            rdata['message'] = "Api key {} was successfully created in {}".format(apikey.name,
                                                                                  apikey.organization.name)
            rdata['success'] = 'success'
        return jsonify(rdata)

    return render_template('manage/apikeys.html')


@app.route('/manage/apikeys/edit', methods=['POST'])
@login_required
def manage_apikey_edit():
    rdata = {'success': False,
             'message': "",
             }
    apikey_id = request.form['pk']
    apikey_field = request.form['name'].strip()
    apikey_new_name = request.form['value'].strip()

    # Check if the user has permission to update this value
    apikey = None
    try:
        apikey = ApiKey.query.get(int(apikey_id))
        if current_user not in apikey.organization.users or apikey is None:
            rdata['success'] = False
            rdata['message'] = "Invalid apikey"
            return jsonify(rdata)

    except Exception:
        logger.exception("Error checking if user ({}) can access the apikey ({})"
                         .format(current_user.id, apikey_id))
        rdata['success'] = False
        rdata['message'] = "Invalid action"
        return jsonify(rdata)

    # Check if the new apikey name can be used
    current_apikey_names = apikey.organization.apikeys
    apikey_list = []
    # Create list of current apikey name to check if the name already exists
    for key in current_apikey_names:
        apikey_list.append(key.name.strip().lower())

    if apikey_new_name.lower() in apikey_list and apikey_new_name.lower() != apikey.name.lower():
        rdata['success'] = False
        rdata['message'] = "Apikey with name `{}` is already in use".format(apikey_new_name)
        return jsonify(rdata)

    # All error checking has been done, lets save the data
    apikey.name = apikey_new_name
    db.session.add(apikey)
    db.session.commit()
    data = [apikey.serialize]
    socketio.emit('manage-apikeys',
                  {'data': data, 'action': 'update'},
                  namespace='/manage/apikeys',
                  room='organization-' + str(apikey.organization.id)
                  )
    rdata['success'] = True

    return jsonify(rdata)


@app.route('/manage/apikeys/delete/<int:apikey_id>', methods=['GET'])
@login_required
def manage_apikey_delete(apikey_id):
    apikey = ApiKey.query.get(apikey_id)
    # Check if user can delete apikey
    if current_user not in apikey.organization.users:
        abort(403)

    db.session.delete(apikey)
    db.session.commit()
    logger.info("User {} deleted API Key {} from {}".format(current_user,
                                                            apikey.name,
                                                            apikey.organization.name))
    data = [apikey.serialize]
    socketio.emit('manage-apikeys',
                  {'data': data, 'action': 'delete'},
                  namespace='/manage/apikeys',
                  room='organization-' + str(apikey.organization.id)
                  )
    return jsonify({'message': "Deleted API key {} from {}"
                               .format(apikey.name, apikey.organization.name),
                    'status': 'success',
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
        join_room('organization-' + str(organization.id))
        for group in organization.groups:
            scrapers = Scraper.query.filter_by(group=group).all()
            scrapers = [i.serialize for i in scrapers]
            scraper_list.extend(scrapers)

    emit('manage-scrapers', {'data': scraper_list, 'action': 'add'})


@app.route('/manage/scrapers', methods=['GET', 'POST'])
@login_required
def manage_scrapers():
    if request.method == 'POST':
        rdata = {'status': 'success',
                 'message': "",
                 }
        name = request.form['name'].strip()
        try:
            group = Group.query.get(int(request.form['group'].strip()))
        except ValueError:
            group = None

        try:
            owner = User.query.get(int(request.form['owner'].strip()))
        except ValueError:
            owner = None

        if not name:
            rdata['message'] = "Name is required"
            rdata['status'] = 'error'

        if group is None:
            rdata['message'] = "Group is required"
            rdata['status'] = 'error'

        elif owner is not None and owner not in group.organization.users:
            # If the user is not in the org that the scraper is in
            rdata['message'] = "Invalid owner for the scraper"
            rdata['status'] = 'error'

        else:
            scraper = Scraper(name)
            scraper.owner = owner
            scraper.group = group

            db.session.add(scraper)
            # Flush to get the id so it can be encoded
            db.session.flush()
            # Do not change the string in the function below.
            # It is just used to create the scraper key, nothing secure
            scraper.key = generate_key(scraper.id, 'Scraper Salt 123')

            db.session.add(scraper)
            db.session.commit()
            logger.info("User {} created scraper {} - {}"
                        .format(current_user.email, scraper.key, scraper.name))
            data = [scraper.serialize]
            socketio.emit('manage-scrapers',
                          {'data': data, 'action': 'add'},
                          namespace='/manage/scrapers',
                          room='organization-' + str(scraper.group.organization.id)
                          )
            rdata['message'] = "Scraper {} was successfully created in group {}"\
                               .format(scraper.name, scraper.group.name)
            rdata['status'] = 'success'
        return jsonify(rdata)

    group_list = []
    for organization in current_user.organizations:
        groups = Group.query.filter_by(organization=organization).all()
        groups = [i.serialize for i in groups]
        group_list.extend(groups)
    return render_template('manage/scrapers.html',
                           groups=group_list,
                           )


@app.route('/manage/scrapers/edit', methods=['POST'])
@login_required
def manage_scraper_edit():
    rdata = {'success': False,
             'message': "",
             'displayAlert': None,
             }
    scraper_id = request.form['pk']
    scraper_field = request.form['name'].strip()
    scraper_new_value = request.form['value'].strip()

    # Check if the user has permission to update this value
    scraper = None
    try:
        scraper = Scraper.query.get(int(scraper_id))
        scraper_users = scraper.group.organization.users
        if current_user not in scraper_users or scraper is None:
            rdata['success'] = False
            rdata['message'] = "Invalid scraper"
            return jsonify(rdata)

    except Exception:
        logger.exception("Error checking if user ({}) can access the scraper ({})"
                         .format(current_user.id, scraper_id))
        rdata['success'] = False
        rdata['message'] = "Invalid action"
        return jsonify(rdata)

    # Checks depending on the field being updated
    if scraper_field == 'name':
        # Scrapers can have the same name
        # All error checking has been done, lets save the data
        scraper.name = scraper_new_value

    elif scraper_field == 'group':
        try:
            new_group = Group.query.get(int(scraper_new_value))
            # Make sure user has permissions for the group
            if current_user not in new_group.organization.users:
                rdata['success'] = False
                rdata['message'] = "Invalid group"
                return jsonify(rdata)

            # Check if the current owner is part of this new group, if not set the owner to current user
            if scraper.owner not in new_group.organization.users:
                rdata['displayAlert'] = {'status': 'warning',
                                         'message': "User <b>{}</b> is not in in the selected organization <b>{}</b>"
                                                    "\nSetting scraper owner to <b>{}</b>"
                                                    .format(scraper.owner.username,
                                                            new_group.organization.name,
                                                            current_user.username,
                                                            ),
                                         }
                # Default owner to current user
                scraper.owner = current_user

            # Set the new group
            scraper.group = new_group

        except Exception:
            logger.exception("Error checking if user ({}) can use the group ({})"
                             .format(current_user.id, scraper_new_value))
            rdata['success'] = False
            rdata['message'] = "Invalid action"
            return jsonify(rdata)

    elif scraper_field == 'owner':
        try:
            new_user = User.query.get(int(scraper_new_value))
            if new_user not in scraper_users or current_user not in scraper_users:
                rdata['success'] = False
                rdata['message'] = "Invalid user"
                return jsonify(rdata)

            # Everything looks good
            scraper.owner = new_user

        except Exception:
            logger.exception("Error checking if user ({}) is in the organization ({})"
                             .format(scraper_new_value, scraper.group.organization.name))
            rdata['success'] = False
            rdata['message'] = "Invalid action"
            return jsonify(rdata)

    db.session.add(scraper)
    db.session.commit()
    logger.info("User {} updated scraper {} - {}"
                .format(current_user.email, scraper.key, scraper.name))
    data = [scraper.serialize]
    socketio.emit('manage-scrapers',
                  {'data': data, 'action': 'update'},
                  namespace='/manage/scrapers',
                  room='organization-' + str(scraper.group.organization.id)
                  )
    rdata['success'] = True

    return jsonify(rdata)


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
                  namespace='/manage/scrapers',
                  room='organization-' + str(scraper.group.organization.id)
                  )
    return jsonify({'message': "Deleted Scraper " + scraper.name, 'status': 'success'})


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
        join_room('organization-' + str(organization.id))
        groups = Group.query.filter_by(organization=organization).all()
        groups = [i.serialize for i in groups]
        group.extend(groups)

    emit('manage-groups', {'data': group, 'action': 'add'})


@app.route('/manage/groups', methods=['GET', 'POST'])
@login_required
def manage_groups():
    if request.method == 'POST':
        rdata = {'status': 'success',
                 'message': '',
                 }
        name = request.form['name'].strip()
        organization_id = request.form['organization'].strip()
        if not name:
            rdata['message'] = "Name is required"
            rdata['status'] = 'error'
        else:
            # Check if group name for organization already exists
            is_group = Group.query.filter_by(organization_id=organization_id).filter_by(name=name).scalar()
            if is_group is not None:
                rdata['message'] = "Group with name {} already exists".format(name)
                rdata['status'] = 'error'
            else:
                # TODO: Make sure current_user has perms to create a group in this organization
                group = Group(name=name, organization_id=organization_id)
                group.organization = Organization.query.get(organization_id)

                db.session.add(group)
                db.session.commit()
                logger.info("User {} created group {} in {}"
                            .format(current_user.email, group.name, group.organization.name))
                data = [group.serialize]
                socketio.emit('manage-groups',
                              {'data': data, 'action': 'add'},
                              namespace='/manage/groups',
                              room='organization-' + str(organization_id)
                              )
                rdata['message'] = "Group {} was successfully created in {}".format(group.name,
                                                                                    group.organization.name)
                rdata['status'] = 'success'
        return jsonify(rdata)

    return render_template('manage/groups.html')


@app.route('/manage/groups/edit', methods=['POST'])
@login_required
def manage_group_edit():
    rdata = {'success': False,
             'message': "",
             }
    group_id = request.form['pk']
    group_field = request.form['name'].strip()
    group_new_name = request.form['value'].strip()

    # Check if the user has permission to update this value
    group = None
    try:
        group = Group.query.get(int(group_id))
        if current_user not in group.organization.users or group is None:
            rdata['success'] = False
            rdata['message'] = "Invalid group"
            return jsonify(rdata)

    except:
        logger.exception("Error checking if user ({}) can access the group ({})"
                         .format(current_user.id, group_id))
        rdata['success'] = False
        rdata['message'] = "Invalid group"
        return jsonify(rdata)

    # Check if the new group name can be used
    current_groups = group.organization.groups
    group_list = []
    # Create list of current groups to check if the name already exists
    for group_name in current_groups:
        group_list.append(group_name.name.strip().lower())

    if group.name.lower() == 'default':
        # Can not rename the default group
        rdata['success'] = False
        rdata['message'] = "Cannot modify the Default group"
        return jsonify(rdata)

    elif (group_new_name.lower() == 'default' or group_new_name.lower() in group_list)\
         and group_new_name.lower() != group.name.lower():
        # There is always a default group, so this name cannot be used
        rdata['success'] = False
        rdata['message'] = "Group with name `{}` is already in use".format(group_new_name)
        return jsonify(rdata)

    # All error checking has been done, lets save the data
    group.name = group_new_name
    db.session.add(group)
    db.session.commit()
    logger.info("User {} updated group {} in {}"
                .format(current_user.email, group.name, group.organization.name))
    data = [group.serialize]
    socketio.emit('manage-groups',
                  {'data': data, 'action': 'update'},
                  namespace='/manage/groups',
                  room='organization-' + str(group.organization_id)
                  )
    rdata['success'] = True

    return jsonify(rdata)


@app.route('/manage/groups/delete/<int:group_id>', methods=['GET'])
@login_required
def manage_group_delete(group_id):
    rdata = {'status': 'error',
             'message': '',
             }
    group = Group.query.get(group_id)
    # Check if user can delete group
    if current_user not in group.organization.users:
        abort(403)

    if group.name.lower() == 'default':
        rdata['message'] = "Cannot delete default group"

    else:
        # If the group has scrapers, move them to the default group
        group_scrapers = list(group.scrapers)
        moved_scrapers_message = ""
        if len(group_scrapers) > 0:
            default_group = Group.query.filter_by(organization_id=group.organization_id)\
                                       .filter_by(name='Default').scalar()

            for scraper in group_scrapers:
                default_group.scrapers.append(scraper)

            db.session.add(default_group)
            moved_scrapers_message = "Moved {num_scrapers} scrapers to the Default group"\
                                     .format(num_scrapers=len(group_scrapers))

        db.session.delete(group)
        db.session.commit()

        rdata['message'] = "Deleted Group {group_name} from {org_name}. {moved_scrapers}"\
                           .format(group_name=group.name,
                                   org_name=group.organization.name,
                                   moved_scrapers=moved_scrapers_message)
        rdata['status'] = 'success'

        logger.info("User {email} deleted group {group_name} from {org_name}"
                    .format(email=current_user.email, group_name=group.name, org_name=group.organization.name))
        data = [group.serialize]
        socketio.emit('manage-groups',
                      {'data': data, 'action': 'delete'},
                      namespace='/manage/groups',
                      room='organization-{org_id}'.format(org_id=group.organization_id)
                      )

    return jsonify(rdata)


###
# Organization Routes
###
@socketio.on('connect', namespace='/manage/organizations')
def connect_manage_organizations():
    if not current_user.is_authenticated:
        # If user is not logged in, deny them access
        return False

    organization_list = []
    for organization in current_user.organizations:
        join_room('organization-' + str(organization.id))
        organization_list.append(organization.serialize)

    emit('manage-organizations', {'data': organization_list, 'action': 'add'})


@app.route('/manage/organizations', methods=['GET', 'POST'])
@login_required
def manage_organizations():
    if request.method == 'POST':
        rdata = {'status': False,
                 'message': '',
                 }
        name = request.form['name'].strip()
        if not name:
            rdata['message'] = "Name is required"
            rdata['status'] = 'error'
        else:
            # Check if organization name already exists
            is_organization = Organization.query.filter_by(name=name).scalar()
            if is_organization is not None:
                rdata['message'] = "Organization with name {} already exists".format(name)
                rdata['status'] = 'error'
            else:
                organization = Organization(name=name, user=current_user)
                db.session.add(organization)
                db.session.flush()
                current_user.organizations.append(organization)
                group = Group(name='Default', organization_id=organization.id)
                db.session.add(group)
                db.session.commit()

                logger.info("User {} created organization {}".format(current_user.username,
                                                                     organization.name))
                data = [organization.serialize]
                # Add current user to the new room
                # TODO: Figure how to join a room here
                # socketio.join_room('organization-' + str(organization.id))
                socketio.emit('manage-organizations',
                              {'data': data, 'action': 'add'},
                              namespace='/manage/organizations',
                              room='organization-' + str(organization.id)
                              )
                rdata['message'] = "Organization {} was successfully created".format(organization.name)
                rdata['status'] = 'success'
        return jsonify(rdata)

    return render_template('manage/organizations.html')


@app.route('/manage/organizations/adduser', methods=['POST'])
@login_required
def manage_organizations_add_user():
    rdata = {'status': False,
             'message': '',
             }
    name = request.form['name'].strip()
    organization_id = request.form['organization'].strip()
    if not name:
        rdata['message'] = "Name is required"
        rdata['status'] = False
        return jsonify(rdata)

    # Check if organization exists
    organization = Organization.query.get(organization_id)
    if organization is None:
        rdata['message'] = "Organization {} - {} does not exists".format(organization_id, name)
        rdata['status'] = 'error'
        return jsonify(rdata)

    # Check if it is the users private organization
    if organization.name == current_user.username:
        rdata['message'] = "Cannot add users to your private organization"
        rdata['status'] = 'error'
        return jsonify(rdata)

    # Does user have permission to be adding users
    if current_user.id != organization.owner_id:
        abort(403)

    new_user = User.query.filter_by(username=name).scalar()
    # Check if new_user is already part of this organization
    if new_user in organization.users:
        rdata['message'] = "User {} is already part of organization {}".format(new_user.username,
                                                                               organization.name)
        rdata['status'] = 'success'
        return jsonify(rdata)

    if new_user is None:
        rdata['message'] = "User {} does not exists".format(name)
        rdata['status'] = 'error'
        return jsonify(rdata)

    new_user.organizations.append(organization)
    db.session.commit()

    logger.info("User {} added user {} to organization {}".format(current_user.username,
                                                                  new_user.username,
                                                                  organization.name))

    rdata['message'] = "User {} was successfully added to {}".format(new_user.username,
                                                                     organization.name)
    rdata['status'] = 'success'
    return jsonify(rdata)


@app.route('/manage/organizations/delete/<int:organization_id>', methods=['GET'])
@login_required
def manage_organizations_delete(organization_id):
    rdata = {'status': 'error',
             'message': '',
             }
    organization = Organization.query.get(organization_id)
    # Check if user can delete group
    if current_user.id != organization.owner_id:
        abort(403)

    # Check if organization has scrapers still assigned to it
    org_has_scrapers = False
    for group in organization.groups:
        if len(list(group.scrapers)) > 0:
            org_has_scrapers = True
            break
    print(org_has_scrapers)

    if organization.name == current_user.username:
        rdata['message'] = "Cannot delete your private organization"

    elif org_has_scrapers is True:
        rdata['message'] = "Cannot delete. Organization has scrapers under it"
        
    else:
        db.session.delete(organization)
        db.session.commit()
        logger.info("User {username} deleted organization {org_name}"
                    .format(username=current_user.username, org_name=organization.name))
        data = [organization.serialize]
        socketio.emit('manage-organizations',
                      {'data': data, 'action': 'delete'},
                      namespace='/manage/organizations',
                      room='organization-{org_id}'.format(org_id=organization.id)
                      )

        rdata['message'] = "Deleted organization {org_name}".format(org_name=organization.name)
        rdata['status'] = 'success'

    return jsonify(rdata)


###############################################################################
###############################################################################
##
#                 Scraper Run Data
##
###############################################################################
###############################################################################
@socketio.on('connect', namespace='/data/scrapers/dev')
def connect_data_scrapers_dev():
    if not current_user.is_authenticated:
        # If user is not logged in, deny them access
        return False

    get_data_scrapers('dev')


@socketio.on('connect', namespace='/data/scrapers/prod')
def connect_data_scrapers_prod():
    if not current_user.is_authenticated:
        # If user is not logged in, deny them access
        return False

    get_data_scrapers('prod')


def get_data_scrapers(environment):
    scraper_list = []
    for organization in current_user.organizations:
        join_room('organization-' + str(organization.id))
        for group in organization.groups:
            for scraper in group.scrapers:
                runs = ScraperRun.query.filter_by(group=group)\
                                       .filter_by(scraper_key=scraper.key)\
                                       .filter_by(environment=environment.upper())\
                                       .order_by(ScraperRun.stop_time.desc())\
                                       .limit(5).all()

                run_list = [i.serialize for i in runs]
                scraper_list.extend(run_list)

    emit('data-scrapers', {'data': scraper_list, 'action': 'add'})


@app.route('/data/scrapers', methods=['GET'])
@login_required
def data_scrapers():
    # Default to prod data
    return redirect(url_for('data_scrapers_env', environment='prod'))


@app.route('/data/scrapers/<string:environment>', methods=['GET'])
@login_required
def data_scrapers_env(environment):
    # print("app", environment)
    if environment not in ['dev', 'prod']:
        abort(404)

    return render_template('data/scrapers.html', environment=environment)
