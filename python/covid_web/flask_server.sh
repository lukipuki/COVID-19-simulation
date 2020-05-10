#!/bin/sh
covid_web.generate_static_rest $DATA_PATH $STATIC_REST_PATH
uwsgi --uid www-data --gid www-data --socket 0.0.0.0:5000 --die-on-term -w covid_web.wsgi:app
