from functools import wraps
from flask import request
import logging
from flask.ext.restful import Resource, abort
from app import socketio, api
from models import *

logger = logging.getLogger(__name__)


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
            organization_id = None
            api_key = request.args['apikey']
            if 'scraperKey' in request.args:
                scraper_key = request.args['scraperKey']
                # Check that the apikey has acccess to the sensor
                organization_id = Scraper.query.filter_by(key=scraper_key).scalar().group.organization.id
            else:
                rdata['message'] = "Missing scraper key"
                return rdata

            key_organization_id = ApiKey.query.filter_by(key=api_key).scalar().organization_id
            if key_organization_id == organization_id:
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
        log.name = log_data['name']
        log.pathname = log_data['pathname']
        log.process = log_data['process']
        log.process_name = log_data['processName']
        log.relative_created = log_data['relativeCreated']
        log.stack_info = log_data['stack_info']
        log.thread = log_data['thread']
        log.thread_name = log_data['threadName']

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
                      namespace='/data/scrapers',
                      room='organization-' + str(log.scraper_run.scraper.group.organization.id)
                      )

        rdata['success'] = True
        rdata['message'] = ""

        return rdata


class APIScraperDataStart(Resource):
    method_decorators = [validate_api_scraper_key, authenticate_api]

    def get(self):
        return {'sddfs': 'adsh'}

    def post(self):
        rdata = {'success': False,
                 'message': ""
                 }

        client_data = request.args
        data = request.json

        group_id = Scraper.query.filter_by(key=client_data['scraperKey']).scalar().group_id

        run = ScraperRun()
        run.scraper_key = client_data['scraperKey']
        run.group_id = group_id
        run.environment = client_data.get('environment')
        run.uuid = client_data['scraperRun']
        run.start_time = data['startTime']

        db.session.add(run)
        db.session.commit()

        data = [run.serialize]
        socketio.emit('data-scrapers',
                      {'data': data, 'action': 'add'},
                      namespace='/data/scrapers',
                      room='organization-' + str(run.scraper.group.organization_id)
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
        run.total_urls = data.get('totalUrls')
        run.num_items_scraped = data.get('itemsScraped')
        run.stop_time = datetime.datetime.strptime(data['stopTime'], "%Y-%m-%d %H:%M:%S.%f")
        # Calc runtime and get counts
        runtime = run.stop_time - run.start_time
        run.runtime = runtime.total_seconds()

        counts = ScraperLog.query.filter_by(run_uuid=client_data['scraperRun'])
        run.critical_count = counts.filter_by(level_name='CRITICAL').count()
        run.error_count = counts.filter_by(level_name='ERROR').count()
        run.warning_count = counts.filter_by(level_name='WARNING').count()

        run.url_error_count = ScraperUrlError.query.filter_by(run_uuid=client_data['scraperRun']).count()

        db.session.commit()

        data = [run.serialize]
        socketio.emit('data-scrapers',
                      {'data': data, 'action': 'update'},
                      namespace='/data/scrapers',
                      room='organization-' + str(run.scraper.group.organization.id)
                      )

        rdata['success'] = True
        rdata['message'] = ""

        return rdata


class APIScraperErrorUrl(Resource):
    method_decorators = [validate_api_scraper_key, authenticate_api]

    def post(self):
        rdata = {'success': False,
                 'message': ""
                 }

        client_data = request.args
        data = request.json

        url_error = ScraperUrlError()
        url_error.run_uuid = client_data['scraperRun']
        url_error.num_tries = data.get('numTries')
        url_error.reason = data.get('reason')
        url_error.ref_id = data.get('ref_id')
        url_error.ref_table = data.get('ref_table')
        url_error.status_code = data.get('statusCode')
        url_error.thread_name = data.get('threadName')
        url_error.url = data.get('url')

        db.session.add(url_error)
        db.session.commit()

        data = [{'rowId': client_data['scraperRun'],
                 'urlErrorCount': 1
                 }]

        socketio.emit('data-scrapers',
                      {'data': data, 'action': 'increment', 'foo': 'bar'},
                      namespace='/data/scrapers',
                      room='organization-' + str(url_error.scraper_run.scraper.group.organization.id)
                      )

        rdata['success'] = True
        rdata['message'] = ""

        return rdata

# Logs from the python logging HTTPHandler
api.add_resource(APIScraperLogging, '/logs')

# General data about the scraper
api.add_resource(APIScraperDataStart, '/data/start')
api.add_resource(APIScraperDataStop, '/data/stop')

# Scraper errors that are not logs
api.add_resource(APIScraperErrorUrl, '/error/url')
