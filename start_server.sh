#!/bin/bash

# 20-questions server startup script with improved logging

# Set environment variables for better logging
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export COLOR_LOGS=${COLOR_LOGS:-1}
export LOG_FILE=${LOG_FILE:-}

# Set up logging format for gunicorn
export PYTHONUNBUFFERED=1

echo "Starting 20-questions server with enhanced logging..."
echo "Log level: $LOG_LEVEL"
echo "Color logs: $COLOR_LOGS"
echo "Log file: ${LOG_FILE:-'(stdout/stderr only)'}"

# Start gunicorn with configuration file
exec gunicorn main:app \
    --config gunicorn.conf.py \
    --log-config-dict '{
        "version": 1,
        "disable_existing_loggers": false,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
            },
            "access": {
                "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "access_console": {
                "class": "logging.StreamHandler", 
                "formatter": "access",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "gunicorn": {
                "level": "'$LOG_LEVEL'",
                "handlers": ["console"],
                "propagate": false
            },
            "gunicorn.access": {
                "level": "'$LOG_LEVEL'",
                "handlers": ["access_console"],
                "propagate": false
            },
            "gunicorn.error": {
                "level": "'$LOG_LEVEL'",
                "handlers": ["console"],
                "propagate": false
            },
            "uvicorn": {
                "level": "'$LOG_LEVEL'",
                "handlers": ["console"],
                "propagate": false
            },
            "uvicorn.access": {
                "level": "'$LOG_LEVEL'",
                "handlers": ["access_console"],
                "propagate": false
            },
            "uvicorn.error": {
                "level": "'$LOG_LEVEL'",
                "handlers": ["console"],
                "propagate": false
            }
        },
        "root": {
            "level": "'$LOG_LEVEL'",
            "handlers": ["console"]
        }
    }'
