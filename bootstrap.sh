#! /bin/bash
set -ex

poetry update
poetry install
poetry run pytest
poetry run python manage.py migrate
# poetry run python manage.py createsuperuser
