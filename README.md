# Scraper Monitor

Developed using Python 3.5 (use at least 3.4.2+)

This project is a way to monitor scrapers. From how long each run takes to any errors it may encounter.
The logs api endpoint is meant to work directly with the python logging `HTTPHandler`.

## Install/Setup

1. `git clone https://github.com/xtream1101/scraper-monitor`
1. `pip3 install -r requirements.txt` Create a python3 virtual environment if you would like
1. Rename `config.py.sample` to `config.py` and edit to reflect the values you need
1. If using postgres, make sure that the schema exists in the database
1. Run `python3 manage.py db migrate` to create/update the database tables
1. Then Run `python3 manage.py db upgrade` to apply those database changes
1. To start the server: `python3 main.py`


## Docker Usage

- TODO


## API Endpoints
_POST data is json_

*Required by all requests:*
- `GET`
  - *All required*
  - `apikey` - Api key of the organization the scraper is under
  - `scraperKey` - Unique id for the scraper
  - `scraperRun` - Unique uuid for this run of the scraper
  - `environment` - Either `DEV` or `PROD`

- Endpoint: `/api/v1/logs`
  - `POST`
    - This is the endpoint the python logging HTTPHandler should be set to
    - Do not log directly to this, use pythons built in logging.

- Endpoint: `/api/v1/data/start`
  - `POST`
    - `startTime` - *Required* - python datetime (should be UTC)

- Endpoint: `/api/v1/data/stop`
  - `POST`
    - `stopTime` - *Required* - python datetime (should be UTC)
    - `totalUrls` - *Optional* - Number of urls that were loaded
    - `refDataCount` - *Optional* - Total number of things that should be scraped
    - `refDataSuccessCount` - *Optional* - Total number of things that did scrape successfully
    - `rowsAddedToDb` - *Optional* - Number of rows add to the database

- Endpoint: `/api/v1/error/url`
  - `POST`
    - `url` - *Required* - The url in question
    - `numTries` - *Optional* - How many times has this url been tried
    - `reason` - *Optional* - Why is the url marked as failed
    - `ref_id` - *Optional* - The ref id of the url
    - `ref_table` - *Optional* - Where does this ref id live
    - `statusCode` - *Optional* - HTTP status code, only needed if this was the cause
    - `threadName` - *Optional* - The name of the python thread.
