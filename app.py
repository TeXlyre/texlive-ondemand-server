from flask import Flask, send_file, make_response, send_from_directory
from threading import Lock
import time
import os.path
import pykpathsea_xetex
import pykpathsea_pdftex
from flask_cors import CORS, cross_origin
import re
import os
import redis
import json

app = Flask(__name__)
redis_client = None

# Configure CORS based on environment variables
api_origins = os.environ.get('API_ORIGINS', '')
if api_origins == '*':
    # Allow all origins
    CORS(app)
elif api_origins:
    # Allow specific origins from the list
    origins = [origin.strip() for origin in api_origins.split(',')]
    CORS(app, resources={r"/*": {"origins": origins}})
else:
    # No CORS - only same origin requests will work
    pass  # Don't initialize CORS at all


def init_redis(redis_url):
    global redis_client
    try:
        redis_client = redis.from_url(redis_url)
        app.logger.info(f"Redis initialized with URL: {redis_url}")
    except Exception as e:
        app.logger.error(f"Failed to initialize Redis: {str(e)}")
        redis_client = None


regex = re.compile(r'[^a-zA-Z0-9 _\-\.]')


def san(name):
    return regex.sub('', name)


def cache_file_info(file_type, format_id, filename, filepath):
    if redis_client:
        cache_key = f"{file_type}:{format_id}:{filename}"
        redis_client.setex(cache_key, 86400, filepath)  # Cache for 24 hours


def get_cached_file_info(file_type, format_id, filename):
    if redis_client:
        cache_key = f"{file_type}:{format_id}:{filename}"
        cached = redis_client.get(cache_key)
        if cached:
            return cached.decode('utf-8')
    return None


@app.route('/xetex/<int:fileformat>/<filename>')
@cross_origin()
def xetex_fetch_file(fileformat, filename):
    filename = san(filename)
    url = None

    # Check cache first
    cached_path = get_cached_file_info('xetex', fileformat, filename)
    if cached_path and os.path.isfile(cached_path):
        url = cached_path
    elif filename == "swiftlatexxetex.fmt" or filename == "xetexfontlist.txt":
        url = filename
    else:
        url = pykpathsea_xetex.find_file(filename, fileformat)
        if url:
            cache_file_info('xetex', fileformat, filename, url)

    if url is None or not os.path.isfile(url):
        return "File not found", 301
    else:
        response = make_response(send_file(url, mimetype='application/octet-stream'))
        response.headers['fileid'] = os.path.basename(url)
        response.headers['Access-Control-Expose-Headers'] = 'fileid'
        return response


@app.route('/pdftex/<int:fileformat>/<filename>')
@cross_origin()
def pdftex_fetch_file(fileformat, filename):
    filename = san(filename)
    url = None

    # Check cache first
    cached_path = get_cached_file_info('pdftex', fileformat, filename)
    if cached_path and os.path.isfile(cached_path):
        url = cached_path
    elif filename == "swiftlatexpdftex.fmt":
        url = filename
    else:
        url = pykpathsea_pdftex.find_file(filename, fileformat)
        if url:
            cache_file_info('pdftex', fileformat, filename, url)

    if url is None or not os.path.isfile(url):
        return "File not found", 301
    else:
        response = make_response(send_file(url, mimetype='application/octet-stream'))
        response.headers['fileid'] = os.path.basename(url)
        response.headers['Access-Control-Expose-Headers'] = 'fileid'
        return response


@app.route('/pdftex/pk/<int:dpi>/<filename>')
@cross_origin()
def pdftex_fetch_pk(dpi, filename):
    filename = san(filename)

    # Check cache first
    cached_path = get_cached_file_info('pdftex_pk', dpi, filename)
    if cached_path and os.path.isfile(cached_path):
        url = cached_path
    else:
        url = pykpathsea_pdftex.find_pk(filename, dpi)
        if url:
            cache_file_info('pdftex_pk', dpi, filename, url)

    if url is None or not os.path.isfile(url):
        return "File not found", 301
    else:
        response = make_response(send_file(url, mimetype='application/octet-stream'))
        response.headers['pkid'] = os.path.basename(url)
        response.headers['Access-Control-Expose-Headers'] = 'pkid'
        return response