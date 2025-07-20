from flask import Flask, send_file, make_response, send_from_directory, request
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

# Import new managers
try:
    from package_manager import PackageManager
    from font_manager import FontManager
except ImportError:
    # Fallback if managers not available
    PackageManager = None
    FontManager = None

app = Flask(__name__)
redis_client = None

# Initialize managers if available
package_manager = PackageManager() if PackageManager else None
font_manager = FontManager() if FontManager else None

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


def initialize_tex_environment():
    """Initialize complete TeX environment"""
    try:
        # Ensure packages are available
        if package_manager:
            package_manager.ensure_packages_available()

        # Update font cache and database
        if font_manager:
            font_manager.update_font_cache()
            font_manager.append_fonts_to_list()

        app.logger.info("TeX environment initialization completed")
        return True
    except Exception as e:
        app.logger.error(f"TeX environment initialization failed: {e}")
        return False


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


# New enhanced endpoints
@app.route('/debug/tex-environment')
@cross_origin()
def debug_tex_environment():
    """Debug endpoint for TeX environment status"""
    try:
        result = {
            'package_manager_available': package_manager is not None,
            'font_manager_available': font_manager is not None
        }

        if package_manager:
            package_info = package_manager.get_package_info()
            result['package_info'] = package_info

            # Test file finding for both engines
            test_files = ['zref-clever.sty', 'amsmath.sty', 'fontspec.sty']
            pdftex_results = {}
            xetex_results = {}

            for filename in test_files:
                # Test pdfTeX finding
                pdftex_path = pykpathsea_pdftex.find_file(filename, 6)  # 6 = tex format
                pdftex_results[filename] = {
                    'found': pdftex_path is not None,
                    'path': pdftex_path
                }

                # Test XeTeX finding
                xetex_path = pykpathsea_xetex.find_file(filename, 6)
                xetex_results[filename] = {
                    'found': xetex_path is not None,
                    'path': xetex_path
                }

            result['pdftex_finding'] = pdftex_results
            result['xetex_finding'] = xetex_results

        if font_manager:
            result['font_count'] = len(font_manager.existing_fonts)

        return result

    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/install-packages', methods=['POST'])
@cross_origin()
def install_packages():
    """Endpoint to install specific packages"""
    try:
        if not package_manager:
            return {'error': 'Package manager not available'}, 500

        data = request.get_json()
        packages = data.get('packages', [])

        if not packages:
            return {'error': 'No packages specified'}, 400

        success = package_manager.install_missing_packages(packages)

        return {
            'success': success,
            'message': f"Installation {'succeeded' if success else 'failed'} for packages: {packages}"
        }

    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/update-fonts', methods=['POST'])
@cross_origin()
def update_fonts():
    """Endpoint to manually update font database"""
    try:
        if not font_manager:
            return {'error': 'Font manager not available'}, 500

        font_manager.update_font_cache()
        font_manager.append_fonts_to_list()
        return {"status": "success", "message": "Fonts updated successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500