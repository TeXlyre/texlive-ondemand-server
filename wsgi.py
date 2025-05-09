from gevent.pywsgi import WSGIServer
from app import app, init_redis
import os

# Initialize Redis if configured
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    init_redis(redis_url)

port = int(os.environ.get('PORT', 5001))
http_server = WSGIServer(('0.0.0.0', port), app)
http_server.serve_forever()