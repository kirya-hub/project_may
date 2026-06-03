#!/usr/bin/env bash

set -o errexit

pip install -r requirements.txt
mkdir -p staticfiles
python manage.py collectstatic --noinput --verbosity 2
python manage.py migrate
