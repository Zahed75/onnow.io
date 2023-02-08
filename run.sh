#!/bin/bash

echo "ONNOW APP SERVER RUN"
pip install -r requirements.txt
python manage.py runserver --settings=$DJANGO_SETTINGS_MODULE 0.0.0.0:8000