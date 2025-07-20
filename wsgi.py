from gevent.pywsgi import WSGIServer
from app import app, init_redis, initialize_tex_environment
import os

# Initialize Redis if configured
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    init_redis(redis_url)

# Initialize complete TeX environment
initialize_tex_environment()

port = int(os.environ.get('PORT', 5000))
http_server = WSGIServer(('0.0.0.0', port), app)
http_server.serve_forever()