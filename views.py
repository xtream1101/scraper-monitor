import logging
from flask import render_template, request, jsonify, abort, redirect, url_for, flash
from flask.ext.security import current_user, login_required
from flask_socketio import emit, join_room
from app import app, socketio
from models import *

logger = logging.getLogger(__name__)


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
                          room='organization-' + str(apikey.organization.id)
                          )
            rdata['message'] = "Api key {} was successfully created in {}".format(apikey.name,
                                                                                  apikey.organization.name)
            rdata['success'] = 'success'
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
    logger.info("User {} deleted API Key {} from {}".format(current_user,
                                                            apikey.name,
                                                            apikey.organization.name))
    data = [apikey.serialize]
    socketio.emit('manage-apikeys',
                  {'data': data, 'action': 'delete'},
                  namespace='/manage/apikeys',
                  room='organization-' + str(apikey.organization.id)
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
                 'message': '',
                 }
        name = request.form['name'].strip()
        group_id = request.form['group'].strip()
        owner = request.form['owner'].strip()
        if not name:
            rdata['message'] = "Name is required"
            rdata['status'] = 'success'
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
                  namespace='/manage/scrapers',
                  room='organization-' + str(scraper.group.organization.id)
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
        db.session.delete(group)
        db.session.commit()
        logger.info("User {} deleted group {} from {}"
                    .format(current_user.email, group.name, group.organization.name))
        data = [group.serialize]
        socketio.emit('manage-groups',
                      {'data': data, 'action': 'delete'},
                      namespace='/manage/groups',
                      room='organization-' + str(group.organization.id)
                      )

        rdata['message'] = "Deleted Group {} from {}".format(group.name, group.organization.name)
        rdata['status'] = 'success'

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

    if organization.name == current_user.username:
        rdata['message'] = "Cannot delete your private organization"
    else:
        db.session.delete(organization)
        db.session.commit()
        logger.info("User {} deleted organization {}"
                    .format(current_user.username, organization.name))
        data = [organization.serialize]
        socketio.emit('manage-organizations',
                      {'data': data, 'action': 'delete'},
                      namespace='/manage/organizations',
                      room='organization-' + str(organization.id)
                      )

        rdata['message'] = "Deleted organization {}".format(organization.name)
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
