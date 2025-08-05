# Gunicorn configuration file
import os
from questions.logging_config import ColorFormatter

# Server socket
bind = "0.0.0.0:8083"
backlog = 2048

# Worker processes
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = False

# Timeout
timeout = 300
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
capture_output = True
enable_stdio_inheritance = True

# Log config
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            '()': ColorFormatter,
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'access': {
            '()': ColorFormatter,
            'format': '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        },
        'access_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'access', 
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'gunicorn': {
            'level': os.environ.get("LOG_LEVEL", "INFO").upper(),
            'handlers': ['console'],
            'propagate': False
        },
        'gunicorn.access': {
            'level': os.environ.get("LOG_LEVEL", "INFO").upper(),
            'handlers': ['access_console'],
            'propagate': False
        },
        'gunicorn.error': {
            'level': os.environ.get("LOG_LEVEL", "INFO").upper(),
            'handlers': ['console'],
            'propagate': False
        },
        'uvicorn': {
            'level': os.environ.get("LOG_LEVEL", "INFO").upper(),
            'handlers': ['console'],
            'propagate': False
        },
        'uvicorn.access': {
            'level': os.environ.get("LOG_LEVEL", "INFO").upper(),
            'handlers': ['access_console'],
            'propagate': False
        },
        'uvicorn.error': {
            'level': os.environ.get("LOG_LEVEL", "INFO").upper(),
            'handlers': ['console'],
            'propagate': False
        }
    },
    'root': {
        'level': os.environ.get("LOG_LEVEL", "INFO").upper(),
        'handlers': ['console']
    }
}

# Process naming
proc_name = "20-questions-app"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting gunicorn server")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading gunicorn server")

def worker_int(worker):
    """Called just after a worker has been killed by a signal."""
    worker.log.info(f"Worker {worker.pid} killed")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker {worker.pid} about to be forked")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker {worker.pid} forked")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info(f"Worker {worker.pid} initialized")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} aborted")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker {worker.pid} exited")

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("Shutting down gunicorn server")
